# app/routees/time_session.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DB
from sqlalchemy import func # Import func for now()
from uuid import UUID
# Make sure timedelta is imported if needed for defaults/calcs
from datetime import datetime, timezone, timedelta
from app.models.time_session import TimeSessionDB, SessionStartIn, SessionStopIn, TimeSessionOut # SessionPauseIn might not be needed now
from app.database.session import get_db

router = APIRouter(prefix="/time_sessions", tags=["time_sessions"])

@router.post("/", response_model=TimeSessionOut, status_code=201)
def start_session(payload: SessionStartIn, db: DB = Depends(get_db)):
    now = datetime.now(timezone.utc)
    sess = TimeSessionDB(
        task_id=payload.task_id,
        goal=payload.goal,
        start_ts=now,
        # --- Initialize New Fields ---
        last_event_ts=now, # Timer starts running immediately
        accumulated_duration=timedelta(0)
        # --- End Init ---
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess

@router.patch("/{session_id}/pause", response_model=TimeSessionOut)
def pause_session(session_id: UUID, db: DB = Depends(get_db)):
    sess = db.get(TimeSessionDB, session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    if sess.end_ts:
        raise HTTPException(status_code=400, detail="Session already stopped")
    if not sess.last_event_ts: # Check if already paused
         raise HTTPException(status_code=400, detail="Session already paused")

    now = datetime.now(timezone.utc)
    # Calculate time elapsed since last start/resume
    elapsed_since_last_event = now - sess.last_event_ts
    # Add it to the accumulated duration
    sess.accumulated_duration += elapsed_since_last_event
    # Mark as paused by setting last_event_ts to None
    sess.last_event_ts = None

    db.commit()
    db.refresh(sess)
    return sess

@router.patch("/{session_id}/resume", response_model=TimeSessionOut)
def resume_session(session_id: UUID, db: DB = Depends(get_db)):
    sess = db.get(TimeSessionDB, session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    if sess.end_ts:
        raise HTTPException(status_code=400, detail="Session already stopped")
    if sess.last_event_ts: # Check if already running
         raise HTTPException(status_code=400, detail="Session already running")

    # Mark as running again by setting last_event_ts to now
    sess.last_event_ts = datetime.now(timezone.utc)

    db.commit()
    db.refresh(sess)
    return sess


@router.patch("/{session_id}/stop", response_model=TimeSessionOut)
def stop_session(session_id: UUID, payload: SessionStopIn, db: DB = Depends(get_db)):
    sess = db.get(TimeSessionDB, session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    if sess.end_ts:
        raise HTTPException(status_code=409, detail="Session already finished")

    now = datetime.now(timezone.utc)
    final_accumulated_duration = sess.accumulated_duration

    # If it was running when stopped, add the last segment
    if sess.last_event_ts:
        elapsed_since_last_event = now - sess.last_event_ts
        final_accumulated_duration += elapsed_since_last_event

    sess.end_ts = now
    sess.outcome = payload.outcome
    sess.duration = final_accumulated_duration # Set the final duration field
    sess.last_event_ts = None # Mark as no longer active

    db.commit()
    db.refresh(sess)
    return sess

# app/routees/time_session.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DB
from uuid import UUID
from datetime import datetime, timezone
from app.models.time_session import TimeSessionDB, SessionStartIn, SessionPauseIn, SessionStopIn, TimeSessionOut
from app.database.session import get_db

router = APIRouter(prefix="/time_sessions", tags=["time_sessions"])
#start a time session
@router.post("/", response_model=TimeSessionOut, status_code=201)
def start_session(payload: SessionStartIn, db: DB = Depends(get_db)):
    sess = TimeSessionDB(
        task_id = payload.task_id,
        goal    = payload.goal,
        start_ts= datetime.now(timezone.utc)
    )
    db.add(sess); db.commit(); db.refresh(sess)
    return sess

#Pause a time session
#ToDO: Add a pause session endpoint

#Stop a time session
@router.patch("/{session_id}/stop", response_model=TimeSessionOut)
def stop_session(session_id: UUID, payload: SessionStopIn, db: DB = Depends(get_db)):
    sess = db.get(TimeSessionDB, session_id)
    if not sess:
        raise HTTPException(404)
    if sess.end_ts:                         # already stopped
        raise HTTPException(409, "Session finished")
    sess.end_ts  = datetime.now(timezone.utc)
    sess.outcome = payload.outcome
    sess.duration = sess.end_ts - sess.start_ts
    db.commit(); db.refresh(sess)
    return sess

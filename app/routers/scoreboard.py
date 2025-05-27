from fastapi import APIRouter, HTTPException, Body, Depends
from datetime import date, datetime, timedelta
from typing import List, Optional
from app.models.scoreboard_models import (
    DailyMilestoneStorage, 
    EveningScoreboardRawInput, 
    ScoreboardTableRow,
    ScoreboardUIPageData,
    ScoreboardMetricTiles,
    DeepWorkSessionData,
    AgentActionStore,
    InputScoreboardMetrics,
    ScoreboardDB,
    AggregatedScoreboardMetrics,
    DailyFocusSummary,
    ScoreboardAggregatedUIPageData
)
# We'll need service functions to interact with the database and perform calculations.
# Let's assume they will be in a module like app.services.scoreboard_service
# from app.services.scoreboard_service import (
#     store_daily_milestone, 
#     process_evening_input, 
#     get_scoreboard_data_for_date,
#     get_deep_work_sessions_for_date,
#     calculate_focus_ratio,
#     get_daily_milestone_for_date,
#     create_full_scoreboard_row
# )
from app.database.session import get_db # Assuming you have a DB session dependency
from sqlalchemy import func as sql_func, cast, Date # To cast date for query
from sqlalchemy.orm import Session # Ensure Session is imported for type hinting

router = APIRouter()

# Placeholder for actual database/service calls
# These would be implemented in app/services/scoreboard_service.py

async def db_store_daily_milestone(entry_date: date, milestone: str, db_session):
    # Placeholder: Save to DB (e.g., a dedicated table or update scoreboard row)
    print(f"[SERVICE_STUB] Storing milestone for {entry_date}: {milestone}")
    # For now, let's assume we have a way to temporarily store/retrieve it for the evening entry.
    # In a real scenario, this would go into a table.
    # For this example, we'll just return it.
    return DailyMilestoneStorage(entry_date=entry_date, daily_milestone=milestone, timestamp=datetime.utcnow())

async def db_get_daily_milestone_for_date(entry_date: date, db_session) -> Optional[str]:
    # Placeholder: Retrieve from DB
    print(f"[SERVICE_STUB] Retrieving milestone for {entry_date}")
    # This is a mock. In reality, you'd query your storage.
    # For this example, let's assume it's not found if not set via the endpoint today.
    return "Placeholder Milestone from DB" # Or None

async def db_get_deep_work_sessions_for_date(entry_date: date, db_session) -> List[DeepWorkSessionData]:
    # Placeholder: Query 'session' table and transform data
    # SELECT COALESCE(SUM(duration_seconds),0)/60 FROM session WHERE work_date = CURRENT_DATE;
    print(f"[SERVICE_STUB] Getting deep work sessions for {entry_date}")
    # Mocking some data
    return [
        DeepWorkSessionData(start_time=datetime(entry_date.year, entry_date.month, entry_date.day, 9, 30), duration_minutes=50),
        DeepWorkSessionData(start_time=datetime(entry_date.year, entry_date.month, entry_date.day, 10, 45), duration_minutes=25),
        DeepWorkSessionData(start_time=datetime(entry_date.year, entry_date.month, entry_date.day, 14, 0), duration_minutes=90),
    ]

async def calculate_focus_ratio(deep_work_sessions: List[DeepWorkSessionData]) -> float:
    total_deep_work_minutes = sum(session.duration_minutes for session in deep_work_sessions)
    # focusRatio = deepWorkMinutes / 480 (assuming 480 minutes = 8 hours workday)
    focus_ratio = total_deep_work_minutes / 480 if 480 > 0 else 0
    return round(min(max(focus_ratio, 0), 1), 3) # Ensure it's between 0 and 1

async def db_store_scoreboard_row(scoreboard_row: ScoreboardTableRow, db_session):
    # Placeholder: Save the complete ScoreboardTableRow to the 'scoreboard' table
    print(f"[SERVICE_STUB] Storing scoreboard row for {scoreboard_row.date}: {scoreboard_row.dict(by_alias=True)}")
    return scoreboard_row # In reality, this would be the object from DB, perhaps with an ID

async def db_get_scoreboard_row_for_date(entry_date: date, db_session) -> Optional[ScoreboardTableRow]:
    # Placeholder: Retrieve a full scoreboard row for a given date
    print(f"[SERVICE_STUB] Getting scoreboard row for {entry_date}")
    # Mocking for now, assuming we just created one.
    # In a real scenario, you'd query the 'scoreboard' table.
    milestone = await db_get_daily_milestone_for_date(entry_date, db_session)
    deep_work = await db_get_deep_work_sessions_for_date(entry_date, db_session)
    focus_ratio_val = await calculate_focus_ratio(deep_work)
    
    # Return a mock if nothing specific is found
    return ScoreboardTableRow(
        date=entry_date,
        netPnL=120.50,
        profitFactor=1.6,
        focusRatio=focus_ratio_val,
        dailyMilestone=milestone if milestone else "Test Milestone",
        milestoneHit=True,
        scheduleAdherence=85.0
    )


@router.post("/morning_checkin", response_model=DailyMilestoneStorage)
async def record_daily_milestone(
    milestone_input: AgentActionStore = Body(...), 
    db_session = Depends(get_db) # Assuming get_db provides a DB session
):
    """
    Handles the morning check-in to store the daily milestone.
    The agent sends: { "action":"store", "field":"dailyMilestone", "value":"<user-text>" }
    """
    if milestone_input.action != "store" or milestone_input.field != "dailyMilestone":
        raise HTTPException(status_code=400, detail="Invalid action or field for milestone.")
    
    today = date.today() # Or derive from input if necessary/allowed
    
    # Store the milestone (this is a simplified placeholder)
    # In a real app, this might go into a temporary store or directly into a 'daily_milestones' table
    # or pre-populate part of today's scoreboard entry.
    stored_milestone = await db_store_daily_milestone(entry_date=today, milestone=milestone_input.value, db_session=db_session)
    
    if not stored_milestone:
        raise HTTPException(status_code=500, detail="Failed to store daily milestone.")
        
    return stored_milestone

@router.post("/evening_scoreboard", response_model=ScoreboardTableRow)
async def record_evening_scoreboard(
    evening_input: EveningScoreboardRawInput = Body(...),
    db_session = Depends(get_db)
):
    """
    Handles the evening scoreboard input.
    - Takes P&L, ProfitFactor, ScheduleAdherence, MilestoneHit.
    - Fetches/calculates focusRatio.
    - Retrieves today's dailyMilestone.
    - Appends a full row to the 'scoreboard' table.
    """
    today = date.today()

    # 1. Get today's daily milestone (should have been set in the morning)
    daily_milestone_text = await db_get_daily_milestone_for_date(today, db_session)
    if not daily_milestone_text:
        # Fallback or error if milestone wasn't set. For now, let's use a default or raise error.
        # Depending on strictness, you might raise HTTPException here.
        daily_milestone_text = "Not set" 
        # raise HTTPException(status_code=400, detail=f"Daily milestone for {today} not found. Please complete morning check-in.")


    # 2. Auto-fetch focus minutes and compute focusRatio
    deep_work_sessions = await db_get_deep_work_sessions_for_date(today, db_session)
    focus_ratio_calculated = await calculate_focus_ratio(deep_work_sessions)

    # 3. Construct the full scoreboard row
    full_row_data = ScoreboardTableRow(
        date=today,
        netPnL=evening_input.netPnL,
        profitFactor=evening_input.profitFactor,
        focusRatio=focus_ratio_calculated,
        dailyMilestone=daily_milestone_text, # Fetched from morning check-in
        milestoneHit=evening_input.milestoneHit,
        scheduleAdherence=evening_input.scheduleAdherence
    )

    # 4. Append row to `scoreboard` table (using a service function)
    stored_row = await db_store_scoreboard_row(full_row_data, db_session)
    if not stored_row:
        raise HTTPException(status_code=500, detail="Failed to store scoreboard entry.")

    # The user spec implies the agent says "Scoreboard updated ✔. Good evening."
    # The API will return the created row. The agent orchestrating this can give the verbal confirmation.
    return stored_row


@router.get("/ui_data/{entry_date}", response_model=ScoreboardUIPageData)
async def get_scoreboard_ui_data_for_date(entry_date: str, db_session = Depends(get_db)):
    """
    Provides all necessary data to render the scoreboard UI for a specific date.
    Includes:
    - The six essential metrics.
    - Data for the deep-work minutes line chart.
    """
    try:
        # Attempt to parse the string date into a date object
        actual_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format for entry_date: '{entry_date}'. Please use YYYY-MM-DD.")

    scoreboard_row = await db_get_scoreboard_row_for_date(actual_date, db_session)
    if not scoreboard_row:
        # Return default/empty structure or 404 if no data for the date
        # For now, providing a default empty view for the metrics
        metric_tiles = ScoreboardMetricTiles()
    else:
        metric_tiles = ScoreboardMetricTiles(
            netPnL=scoreboard_row.netPnL,
            profitFactor=scoreboard_row.profitFactor,
            focusRatio=scoreboard_row.focusRatio,
            dailyMilestone=scoreboard_row.dailyMilestone,
            milestoneHit=scoreboard_row.milestoneHit,
            scheduleAdherence=scoreboard_row.scheduleAdherence
        )
    
    deep_work_data = await db_get_deep_work_sessions_for_date(actual_date, db_session)

    return ScoreboardUIPageData(
        entry_date=actual_date, # Use the parsed date object here
        metrics=metric_tiles,
        deep_work_chart_data=deep_work_data
    )

@router.get("/ui_data_today", response_model=ScoreboardUIPageData)
async def get_scoreboard_ui_data_for_today(db_session = Depends(get_db)):
    """
    Provides all necessary data to render the scoreboard UI for today.
    """
    today = date.today()
    return await get_scoreboard_ui_data_for_date(entry_date=today.strftime("%Y-%m-%d"), db_session=db_session)

@router.get("/ui_data_period", response_model=ScoreboardAggregatedUIPageData)
async def get_scoreboard_ui_data_for_period(
    start_date_str: str, 
    end_date_str: str, 
    db: Session = Depends(get_db)
):
    """
    Provides aggregated scoreboard data for a given date range (e.g., week or month).
    Calculates averages for metrics and daily sums for deep work.
    """
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD.")

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date cannot be after end date.")

    # Query for records within the date range
    # Note: ScoreboardDB.date is DateTime, so we cast it to Date for comparison
    query = db.query(ScoreboardDB).filter(
        cast(ScoreboardDB.date, Date) >= start_date,
        cast(ScoreboardDB.date, Date) <= end_date
    )
    
    period_records = query.all()

    # VVVVVV ADD THIS DEBUG BLOCK VVVVVV
    print(f"--- PERIOD DATA DEBUG ---")
    print(f"Attempting to fetch data for period: {start_date_str} to {end_date_str}")
    # To print the query, you need to compile it for your specific dialect.
    # This is a general way to see it; for PostgreSQL, it would be:
    # from sqlalchemy.dialects import postgresql
    # print(f"SQLAlchemy Query: {str(query.statement.compile(dialect=postgresql.dialect()))}")
    # For a simpler view that usually works for basic queries:
    print(f"SQLAlchemy Query (approximate): {str(query)}") 
    print(f"Number of records found in DB for this period: {len(period_records)}")
    if period_records:
        print(f"Details of records found:")
        for r_idx, r_val in enumerate(period_records):
            print(f"  Record {r_idx+1}: Date_DB='{r_val.date}', PnL='{r_val.net_pnl}', FocusRatio='{r_val.focus_ratio}'")
    else:
        print(f"  No records were found in the database for the specified period.")
    print(f"--- END PERIOD DATA DEBUG ---")
    # ^^^^^^ END OF DEBUG BLOCK ^^^^^^

    if not period_records:
        # Return a default empty structure if no data for the period
        return ScoreboardAggregatedUIPageData(
            period_description=f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}",
            metrics=AggregatedScoreboardMetrics(), # Empty/default metrics
            deep_work_chart_data=[]
        )

    # Calculate aggregated metrics
    total_records = len(period_records)
    avg_net_pnl = sum(r.net_pnl for r in period_records if r.net_pnl is not None) / total_records if total_records else None
    avg_profit_factor = sum(r.profit_factor for r in period_records if r.profit_factor is not None) / total_records if total_records else None
    avg_focus_ratio = sum(r.focus_ratio for r in period_records if r.focus_ratio is not None) / total_records if total_records else None
    avg_schedule_adherence = sum(r.schedule_adherence for r in period_records if r.schedule_adherence is not None) / total_records if total_records else None
    
    milestones_hit_count = sum(1 for r in period_records if r.milestone_hit is True)
    milestone_completion_rate = milestones_hit_count / total_records if total_records else None

    # For periodDailyMilestoneDescription, let's try to get the latest one that's not null/empty
    latest_milestone_desc = "Multiple Milestones or N/A"
    # Sort records by date descending to find the latest milestone
    sorted_records_for_milestone = sorted(period_records, key=lambda r: r.date, reverse=True)
    for r in sorted_records_for_milestone:
        if r.daily_milestone and r.daily_milestone.strip() and r.daily_milestone != "N/A":
            latest_milestone_desc = r.daily_milestone
            break

    aggregated_metrics = AggregatedScoreboardMetrics(
        avgNetPnL=avg_net_pnl,
        avgProfitFactor=avg_profit_factor,
        avgFocusRatio=avg_focus_ratio,
        avgScheduleAdherence=avg_schedule_adherence,
        milestoneCompletionRate=milestone_completion_rate,
        periodDailyMilestoneDescription=latest_milestone_desc
    )

    # Prepare deep_work_chart_data: list of {date, totalDeepWorkMinutes}
    # Group records by date first for deep work calculation
    daily_deep_work_data: List[DailyFocusSummary] = []
    # Create all dates in the range to ensure chart has entries even for days with no data
    current_date_iter = start_date
    all_dates_in_period = []
    while current_date_iter <= end_date:
        all_dates_in_period.append(current_date_iter)
        current_date_iter += timedelta(days=1) # Requires: from datetime import timedelta

    # Initialize deep work minutes for all dates in the period to 0
    deep_work_map = {day.strftime("%Y-%m-%d"): 0.0 for day in all_dates_in_period}

    for record in period_records:
        record_date_str = record.date.strftime("%Y-%m-%d")
        # focus_ratio is 0-1, workday is 480 minutes. Allow null focus_ratio.
        deep_work_minutes_for_day_decimal = (record.focus_ratio * 480) if record.focus_ratio is not None else 0
        deep_work_minutes_for_day_float = float(deep_work_minutes_for_day_decimal) # Convert to float
        
        if record_date_str in deep_work_map:
            deep_work_map[record_date_str] += deep_work_minutes_for_day_float # Now adding float to float
        # else: # This case should ideally not happen if all_dates_in_period covers the record dates
            # deep_work_map[record_date_str] = deep_work_minutes_for_day_float
    
    for date_obj in all_dates_in_period:
        daily_deep_work_data.append(
            DailyFocusSummary(date=date_obj, totalDeepWorkMinutes=deep_work_map[date_obj.strftime("%Y-%m-%d")])
        )

    return ScoreboardAggregatedUIPageData(
        period_description=f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}",
        metrics=aggregated_metrics,
        deep_work_chart_data=daily_deep_work_data
    )

@router.post("/metrics/{entry_date}", response_model=ScoreboardTableRow)
async def upsert_scoreboard_metrics_for_date(
    entry_date: str,
    metrics_input: InputScoreboardMetrics = Body(...),
    db_session = Depends(get_db)
):
    """
    Creates or updates a scoreboard entry for the given date with the provided metrics.
    """
    try:
        actual_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format for entry_date: '{entry_date}'. Use YYYY-MM-DD.")

    # Query for an existing record for the specific date part of the DateTime column
    # This assumes your ScoreboardDB.date column is a DateTime type.
    # We need to compare only the date part.
    existing_record = db_session.query(ScoreboardDB).filter(sql_func.date(ScoreboardDB.date) == actual_date).first()

    if existing_record:
        # Update existing record
        if metrics_input.netPnL is not None:
            existing_record.net_pnl = metrics_input.netPnL
        if metrics_input.profitFactor is not None:
            existing_record.profit_factor = metrics_input.profitFactor
        if metrics_input.focusRatio is not None:
            existing_record.focus_ratio = metrics_input.focusRatio # Allow user to set focus ratio directly
        if metrics_input.dailyMilestone is not None:
            existing_record.daily_milestone = metrics_input.dailyMilestone
            # If dailyMilestone is being set or changed, update its timestamp
            existing_record.milestone_time_set = datetime.utcnow() 
        if metrics_input.milestoneHit is not None:
            existing_record.milestone_hit = metrics_input.milestoneHit
        if metrics_input.scheduleAdherence is not None:
            existing_record.schedule_adherence = metrics_input.scheduleAdherence
        
        # If daily_milestone was set to empty string or None and it was previously populated, consider if milestone_time_set needs clearing or special handling
        # For now, we only update milestone_time_set if dailyMilestone is provided and not None.
        if metrics_input.dailyMilestone is None and existing_record.daily_milestone is not None:
            # Policy: if user explicitly clears milestone, what happens to time_set? For now, leave as is, or set to now.
            # Let's assume clearing milestone text keeps the last time_set for historical reasons unless specified otherwise.
            pass 

        print(f"Updating record for {actual_date}")
    else:
        # Create new record
        # Ensure all NOT NULL fields in ScoreboardDB are handled
        # Default milestone_time_set if daily_milestone is provided, otherwise it might need to be nullable or have a sensible default in the DB model if no milestone given
        milestone_time_to_set = datetime.utcnow() if metrics_input.dailyMilestone is not None else datetime.utcnow() # Default to now, or handle if nullable
        
        # If daily_milestone is None, the DB field must be nullable or have a default. 
        # Assuming daily_milestone in DB cannot be null based on ScoreboardDB model in search results.
        # And milestone_time_set also cannot be null.
        
        new_data = {
            "date": datetime.combine(actual_date, datetime.min.time()), # Store as datetime
            "net_pnl": metrics_input.netPnL if metrics_input.netPnL is not None else 0.0,
            "profit_factor": metrics_input.profitFactor if metrics_input.profitFactor is not None else 0.0,
            "focus_ratio": metrics_input.focusRatio if metrics_input.focusRatio is not None else 0.0,
            "daily_milestone": metrics_input.dailyMilestone if metrics_input.dailyMilestone is not None else "N/A", # DB requires non-null
            "milestone_hit": metrics_input.milestoneHit if metrics_input.milestoneHit is not None else False,
            "schedule_adherence": metrics_input.scheduleAdherence if metrics_input.scheduleAdherence is not None else 0.0,
            "milestone_time_set": milestone_time_to_set
        }
        existing_record = ScoreboardDB(**new_data)
        db_session.add(existing_record)
        print(f"Creating new record for {actual_date}") 

    try:
        db_session.commit()
        db_session.refresh(existing_record)
    except Exception as e:
        db_session.rollback()
        print(f"Error during DB commit: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Convert the SQLAlchemy model (ScoreboardDB) to the Pydantic model (ScoreboardTableRow)
    # The ScoreboardTableRow model might expect a `date` field of type `date` not `datetime`.
    # The ScoreboardDB model has `date` as DateTime.
    return ScoreboardTableRow(
        date=existing_record.date.date(), # Convert datetime to date for ScoreboardTableRow
        netPnL=float(existing_record.net_pnl),
        profitFactor=float(existing_record.profit_factor),
        focusRatio=float(existing_record.focus_ratio),
        dailyMilestone=existing_record.daily_milestone,
        milestoneHit=existing_record.milestone_hit,
        scheduleAdherence=float(existing_record.schedule_adherence)
    )

# Need to ensure this router is included in the main FastAPI app
# e.g., in app/main.py:
# from app.api.v1.endpoints import scoreboard
# app.include_router(scoreboard.router, prefix="/api/v1/scoreboard", tags=["scoreboard"])

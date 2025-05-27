from sqlalchemy import Column, Text, DateTime, Boolean, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
import uuid

class ScoreboardDB(Base):
    """Database model for daily scoreboard entries."""
    __tablename__ = "scoreboard"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    net_pnl = Column(Numeric(10, 2), nullable=False)  # CAD currency
    profit_factor = Column(Numeric(5, 2), nullable=False)
    focus_ratio = Column(Numeric(5, 2), nullable=False)  # Stored as decimal (0-1)
    milestone_hit = Column(Boolean, nullable=False)
    schedule_adherence = Column(Numeric(5, 2), nullable=False)  # Percentage
    daily_milestone = Column(Text, nullable=False)
    milestone_time_set = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ScoreboardCreate(BaseModel):
    """Pydantic model for creating a new scoreboard entry."""
    net_pnl: float = Field(..., description="Net P&L in CAD")
    profit_factor: float = Field(..., description="Profit factor")
    focus_ratio: float = Field(..., description="Focus ratio as decimal (0-1)")
    milestone_hit: bool = Field(..., description="Whether daily milestone was hit")
    schedule_adherence: float = Field(..., description="Schedule adherence percentage")
    daily_milestone: str = Field(..., description="The daily milestone text")
    milestone_time_set: datetime = Field(..., description="When the milestone was set")

class ScoreboardOut(BaseModel):
    """Pydantic model for scoreboard output."""
    id: uuid.UUID
    date: datetime
    net_pnl: float
    profit_factor: float
    focus_ratio: float
    milestone_hit: bool
    schedule_adherence: float
    daily_milestone: str
    milestone_time_set: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class DailyMilestone(BaseModel):
    # Model for storing the daily milestone
    daily_milestone: str = Field(..., description="The user's stated single daily milestone.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the milestone was recorded.")

class ScoreboardEntryBase(BaseModel):
    # Base model for a scoreboard entry's core metrics
    net_pnl: Optional[float] = Field(None, alias="netPnL", description="Net Profit and Loss in CAD.")
    profit_factor: Optional[float] = Field(None, alias="profitFactor", description="Profit factor as a decimal.")
    schedule_adherence: Optional[float] = Field(None, description="Stick-to-schedule percentage (0-100).")
    milestone_hit: Optional[bool] = Field(None, description="Was today's milestone completed? (yes/no).")

class ScoreboardEntryCreate(ScoreboardEntryBase):
    # Model used when creating/logging a new scoreboard entry at the end of the day
    # focusRatio is calculated, dailyMilestone is pulled from morning check-in
    pass

class ScoreboardEntry(ScoreboardEntryBase):
    # Full scoreboard entry model, including auto-calculated and morning-derived fields
    id: Optional[int] = Field(None, description="Unique ID of the scoreboard entry.")
    entry_date: date = Field(..., alias="date", description="The date of the scoreboard entry.")
    focus_ratio: Optional[float] = Field(None, alias="focusRatio", ge=0, le=1, description="Focus ratio (0-1), auto-calculated.")
    daily_milestone: Optional[str] = Field(None, description="The daily milestone for this date.")
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class ScoreboardUIRefreshData(BaseModel):
    # Model for data required to refresh the UI dashboard
    metrics: ScoreboardEntry
    # We'll need to define what 'deep_work_chart_data' looks like.
    # For now, let's assume it's a list of points (e.g., time and duration).
    deep_work_chart_data: list[dict] = Field(..., description="Data for the deep-work minutes line chart.")

# The user provided a JSON structure for assistant interactions.
# Let's model those as well for clarity, though they might be handled directly by the agent logic.

class AssistantStoreAction(BaseModel):
    action: str = "store"
    field: str
    value: str # This could be more specific if we knew all possible fields
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EveningScoreboardInput(BaseModel):
    # Model to capture user input for the evening scoreboard
    net_pnl: float = Field(..., alias="netPnL")
    profit_factor: float = Field(..., alias="profitFactor")
    schedule_adherence: float # Percentage
    milestone_hit: bool

class ScoreboardFullRow(BaseModel):
    # This matches the final JSON to be appended to the 'scoreboard' table
    date: date
    netPnL: float
    profitFactor: float
    focusRatio: float
    dailyMilestone: str
    milestoneHit: bool
    scheduleAdherence: float

class DailyMilestoneStorage(BaseModel):
    # Model for how the daily milestone might be stored or retrieved internally
    # This aligns with the agent's action to store { "field":"dailyMilestone", "value":"<user-text>" }
    # We assume it will be stored against a specific date.
    entry_date: date = Field(default_factory=date.today)
    daily_milestone: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ScoreboardMetricTiles(BaseModel):
    # Model for the six essential metrics to be displayed as tiles
    netPnL: Optional[float] = None
    profitFactor: Optional[float] = None
    focusRatio: Optional[float] = None
    dailyMilestone: Optional[str] = None
    milestoneHit: Optional[bool] = None
    scheduleAdherence: Optional[float] = None # Percentage

class DeepWorkSessionData(BaseModel):
    # Represents a single session for the deep work chart
    # Assuming time is on x-axis and duration on y-axis for a specific day
    # For simplicity, let's say time is just hour, and duration is in minutes for that hour block
    # This will need refinement based on how `session` table stores data.
    start_time: datetime # Or just time if all on the same day
    duration_minutes: float

class ScoreboardUIPageData(BaseModel):
    # Data needed to render the entire scoreboard page for a specific date
    entry_date: date
    metrics: ScoreboardMetricTiles
    deep_work_chart_data: list[DeepWorkSessionData] # e.g., list of (timestamp, duration_minutes)

# Models for agent interaction, as per user spec

class AgentActionStore(BaseModel):
    action: str = "store"
    field: str # e.g., "dailyMilestone"
    value: str # The actual text from the user
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EveningScoreboardRawInput(BaseModel):
    # Raw input collected by the agent for the evening scoreboard
    netPnL: float
    profitFactor: float
    scheduleAdherence: float # Percentage 0-100
    milestoneHit: bool # true if yes, false if no

class ScoreboardTableRow(BaseModel):
    # This strictly matches the JSON structure for a row in the 'scoreboard' table
    date: date
    netPnL: float
    profitFactor: float
    focusRatio: float # Calculated: deepWorkMinutes / 480
    dailyMilestone: str
    milestoneHit: bool
    scheduleAdherence: float # Percentage 0-100

    class Config:
        allow_population_by_field_name = True # Allows using netPnL etc.

# New model for direct input from the ScoreboardPage form
class InputScoreboardMetrics(BaseModel):
    netPnL: Optional[float] = Field(None, alias="netPnL", description="Net Profit and Loss in CAD.")
    profitFactor: Optional[float] = Field(None, alias="profitFactor", description="Profit factor as a decimal.")
    focusRatio: Optional[float] = Field(None, alias="focusRatio", ge=0, le=1, description="Focus ratio (0-1), user input.")
    dailyMilestone: Optional[str] = Field(None, description="The daily milestone for this date.") # Changed from default empty string to allow explicit None
    milestoneHit: Optional[bool] = Field(None, description="Was today's milestone completed? (yes/no).")
    scheduleAdherence: Optional[float] = Field(None, description="Stick-to-schedule percentage (0-100).")

    class Config:
        allow_population_by_field_name = True 

# --- Models for Aggregated Period Data (Week/Month) --- #

class AggregatedScoreboardMetrics(BaseModel):
    """Metrics that are averaged or summarized over a period."""
    avgNetPnL: Optional[float] = Field(None, description="Average Net P&L over the period.")
    avgProfitFactor: Optional[float] = Field(None, description="Average Profit Factor over the period.")
    avgFocusRatio: Optional[float] = Field(None, description="Average Focus Ratio (0-1) over the period.")
    avgScheduleAdherence: Optional[float] = Field(None, description="Average Schedule Adherence (%) over the period.")
    milestoneCompletionRate: Optional[float] = Field(None, description="Percentage of milestones hit (0-1) over the period.")
    # For dailyMilestone, we might just show a generic message or latest if easily queryable
    periodDailyMilestoneDescription: Optional[str] = Field("Multiple Milestones", description="Description for daily milestones over the period.")

class DailyFocusSummary(BaseModel):
    """Summary of deep work for a single day, used in period charts."""
    date: date
    totalDeepWorkMinutes: float

class ScoreboardAggregatedUIPageData(BaseModel):
    """Data needed to render the scoreboard UI for an aggregated period (week/month)."""
    period_description: str # e.g., "Week of May 26 - Jun 01, 2025" or "May 2025"
    metrics: AggregatedScoreboardMetrics
    deep_work_chart_data: List[DailyFocusSummary] 
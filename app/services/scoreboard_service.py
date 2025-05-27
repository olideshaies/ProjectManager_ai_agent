from datetime import datetime, time
from sqlalchemy.orm import Session
from app.models.scoreboard_models import ScoreboardDB, ScoreboardCreate
from app.routers.scoreboard import calculate_focus_ratio
from app.database.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

class ScoreboardService:
    """Service class to handle daily scoreboard operations."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        self.db.close()
    
    def set_daily_milestone(self, milestone: str) -> ScoreboardDB:
        """Set the daily milestone in the morning."""
        try:
            # Check if entry already exists for today
            today = datetime.now().date()
            existing = self.db.query(ScoreboardDB).filter(
                func.date(ScoreboardDB.date) == today
            ).first()
            
            if existing:
                existing.daily_milestone = milestone
                existing.milestone_time_set = datetime.now()
                self.db.commit()
                return existing
            
            # Create new entry
            new_entry = ScoreboardDB(
                daily_milestone=milestone,
                milestone_time_set=datetime.now(),
                net_pnl=0.0,
                profit_factor=0.0,
                focus_ratio=0.0,
                milestone_hit=False,
                schedule_adherence=0.0
            )
            self.db.add(new_entry)
            self.db.commit()
            self.db.refresh(new_entry)
            return new_entry
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error setting daily milestone: {str(e)}")
            raise
    
    def update_evening_metrics(
        self,
        net_pnl: float,
        profit_factor: float,
        schedule_adherence: float,
        milestone_hit: bool
    ) -> ScoreboardDB:
        """Update evening metrics and calculate focus ratio."""
        try:
            today = datetime.now().date()
            entry = self.db.query(ScoreboardDB).filter(
                func.date(ScoreboardDB.date) == today
            ).first()
            
            if not entry:
                raise ValueError("No scoreboard entry found for today")
            
            # Calculate focus ratio
            focus_ratio = calculate_focus_ratio(self.db, datetime.now())
            
            # Update metrics
            entry.net_pnl = net_pnl
            entry.profit_factor = profit_factor
            entry.focus_ratio = focus_ratio
            entry.schedule_adherence = schedule_adherence
            entry.milestone_hit = milestone_hit
            
            self.db.commit()
            self.db.refresh(entry)
            return entry
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating evening metrics: {str(e)}")
            raise
    
    def format_scoreboard_entry(self, entry: ScoreboardDB) -> str:
        """Format a scoreboard entry for display."""
        focus_percent = entry.focus_ratio * 100
        warning = "⚠️" if not entry.milestone_hit else ""
        
        return f"""
Daily Scoreboard {warning}
-------------------
Date: {entry.date.strftime('%Y-%m-%d')}
Net P&L: ${entry.net_pnl:.2f} CAD
Profit Factor: {entry.profit_factor:.2f}
Focus Ratio: {focus_percent:.1f}%
Schedule Adherence: {entry.schedule_adherence:.1f}%
Daily Milestone: {entry.daily_milestone}
Milestone Status: {'✅' if entry.milestone_hit else '❌'}
""" 
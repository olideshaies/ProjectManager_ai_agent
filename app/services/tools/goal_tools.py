import logging
from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.goal_models import GoalDB, GoalCreate, GoalOut
from app.database.session import SessionLocal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def get_db():
    """Get a database session"""
    db = SessionLocal()
    try:
        logger.info(f"Database session created: {db}")
        # Test a simple query
        test_count = db.query(GoalDB).count()
        logger.info(f"Database contains {test_count} goals total")
        return db
    finally:
        db.close()

def create_goal(goal_data: GoalCreate) -> GoalOut:
    """
    Creates a new goal in the database
    """
    db = get_db()
    try:
        # Create new goal object
        new_goal = GoalDB(
            title=goal_data.title,
            description=goal_data.description,
            completed=goal_data.completed,
            target_date=goal_data.target_date
        )
        
        # Add to database and commit
        db.add(new_goal)
        db.commit()
        db.refresh(new_goal)
        
        # Return as GoalOut model
        return GoalOut(
            id=new_goal.id,
            title=new_goal.title,
            description=new_goal.description,
            completed=new_goal.completed,
            target_date=new_goal.target_date,
            created_at=new_goal.created_at,
            updated_at=new_goal.updated_at
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating goal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create goal: {str(e)}")
    finally:
        db.close()

def get_goal(goal_id: str) -> GoalOut:
    """
    Retrieves a goal by ID
    """
    db = get_db()
    try:
        # Convert string ID to UUID if necessary
        if isinstance(goal_id, str):
            goal_id = uuid.UUID(goal_id)
            
        goal = db.query(GoalDB).filter(GoalDB.id == goal_id).first()
        if not goal:
            raise HTTPException(status_code=404, detail=f"Goal with id {goal_id} not found")
            
        return GoalOut(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            completed=goal.completed,
            target_date=goal.target_date,
            created_at=goal.created_at,
            updated_at=goal.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving goal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve goal: {str(e)}")
    finally:
        db.close()

def list_goals() -> List[GoalOut]:
    """
    Lists all goals
    """
    db = get_db()
    try:
        goals = db.query(GoalDB).all()
        return [
            GoalOut(
                id=goal.id,
                title=goal.title,
                description=goal.description,
                completed=goal.completed,
                target_date=goal.target_date,
                created_at=goal.created_at,
                updated_at=goal.updated_at
            ) for goal in goals
        ]
    except Exception as e:
        logger.error(f"Error listing goals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list goals: {str(e)}")
    finally:
        db.close()

def update_goal(goal_data) -> GoalOut:
    """
    Updates a goal based on provided data
    The goal_data object should have an id and any fields to update
    """
    db = get_db()
    try:
        # Convert string ID to UUID if necessary
        if isinstance(goal_data.id, str):
            goal_id = uuid.UUID(goal_data.id)
        else:
            goal_id = goal_data.id
            
        goal = db.query(GoalDB).filter(GoalDB.id == goal_id).first()
        if not goal:
            raise HTTPException(status_code=404, detail=f"Goal with id {goal_id} not found")
        
        # Update fields if provided in the input
        if hasattr(goal_data, 'title') and goal_data.title is not None:
            goal.title = goal_data.title
        if hasattr(goal_data, 'description') and goal_data.description is not None:
            goal.description = goal_data.description
        if hasattr(goal_data, 'completed') and goal_data.completed is not None:
            goal.completed = goal_data.completed
        if hasattr(goal_data, 'target_date') and goal_data.target_date is not None:
            goal.target_date = goal_data.target_date
            
        db.commit()
        db.refresh(goal)
        
        return GoalOut(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            completed=goal.completed,
            target_date=goal.target_date,
            created_at=goal.created_at,
            updated_at=goal.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating goal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update goal: {str(e)}")
    finally:
        db.close()

def delete_goal(goal_id: str):
    """
    Deletes a goal by ID
    Returns a confirmation message
    """
    db = get_db()
    try:
        logger.info(f"Attempting to delete goal with ID: {goal_id}")
        # Convert string ID to UUID if necessary
        try:
            if isinstance(goal_id, str):
                logger.info(f"Converting string ID {goal_id} to UUID")
                goal_id = uuid.UUID(goal_id)
        except ValueError:
            logger.error(f"Invalid UUID format: {goal_id}")
            raise HTTPException(status_code=400, detail=f"Invalid UUID format: {goal_id}")
            
        goal = db.query(GoalDB).filter(GoalDB.id == goal_id).first()
        if not goal:
            raise HTTPException(status_code=404, detail=f"Goal with id {goal_id} not found")
            
        logger.info(f"Found goal: {goal.title} with ID: {goal.id}")
        goal_title = goal.title
        db.delete(goal)
        db.commit()
        logger.info(f"Goal deleted, committing transaction")
        
        # After committing the deletion
        verification = db.query(GoalDB).filter(GoalDB.id == goal_id).first()
        if verification:
            logger.warning(f"Goal still exists after deletion attempt!")
        else:
            logger.info(f"Goal successfully deleted (verified)")
        
        # Return a simple response object
        return type('GoalDelete', (), {
            'id': str(goal_id),
            'message': f"Goal '{goal_title}' deleted successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting goal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete goal: {str(e)}")
    finally:
        db.close()
        logger.info(f"Transaction committed successfully")

def search_goals_by_subject(subject: str, limit: int = 10) -> List[GoalOut]:
    """
    Searches for goals where the title contains the subject string
    """
    db = get_db()
    try:
        goals = db.query(GoalDB).filter(GoalDB.title.ilike(f"%{subject}%")).limit(limit).all()
        
        return [
            GoalOut(
                id=goal.id,
                title=goal.title,
                description=goal.description,
                completed=goal.completed,
                target_date=goal.target_date,
                created_at=goal.created_at,
                updated_at=goal.updated_at
            ) for goal in goals
        ]
    except Exception as e:
        logger.error(f"Error searching goals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search goals: {str(e)}")
    finally:
        db.close() 
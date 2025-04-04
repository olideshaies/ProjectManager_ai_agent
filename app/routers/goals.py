# app/routers/goals.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.session import SessionLocal
from app.models.goal_models import GoalDB, GoalCreate, GoalOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=GoalOut)
def create_goal(goal_data: GoalCreate, db: Session = Depends(get_db)):
    """
    Create a new goal in the 'goals' table.
    """
    new_goal = GoalDB(
        title=goal_data.title,
        description=goal_data.description,
        completed=goal_data.completed,
        target_date=goal_data.target_date
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal


@router.get("/", response_model=List[GoalOut])
def list_goals(db: Session = Depends(get_db)):
    """
    List all goals.
    """
    goals = db.query(GoalDB).all()
    return goals


@router.get("/{goal_id}", response_model=GoalOut)
def get_goal(goal_id: str, db: Session = Depends(get_db)):
    goal = db.query(GoalDB).get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal

@router.delete("/{goal_id}")
def delete_goal(goal_id: str, db: Session = Depends(get_db)):
    goal = db.query(GoalDB).get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return {"message": f"Goal {goal_id} deleted."}

@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: str, updates: GoalCreate, db: Session = Depends(get_db)):
    """
    Partial update: any field in GoalCreate can be used to update the existing record.
    """
    goal = db.query(GoalDB).get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if updates.title is not None:
        goal.title = updates.title
    if updates.description is not None:
        goal.description = updates.description
    if updates.completed is not None:
        goal.completed = updates.completed
    if updates.target_date is not None:
        goal.target_date = updates.target_date

    db.commit()
    db.refresh(goal)
    return goal

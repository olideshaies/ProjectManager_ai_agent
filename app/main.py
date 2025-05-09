from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from app.routers import voice, tasks, goals, time_session
from app.services.agent_flow import run_agent_flow
from app.database.base import Base
from app.database.session import engine
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Voice Command API")

# Create the database tables
Base.metadata.create_all(bind=engine)

# Include your API routers
app.include_router(voice.router)
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])  # Add tasks router
app.include_router(goals.router, prefix="/goals", tags=["goals"]) # Add goals router
app.include_router(time_session.router)  # Add time_sessions router

# Mount the static UI directory last so API routes are matched first
# app.mount("/", StaticFiles(directory="static/ui/dist", html=True), name="ui")

@app.post("/agent")
async def agent_endpoint(request: Request):
    body = await request.json()
    user_query = body.get("user_query")
    if not user_query:
        raise HTTPException(status_code=400, detail="user_query is required")
    return run_agent_flow(user_query)
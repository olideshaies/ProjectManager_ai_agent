from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from app.routers import voice, tasks  # Import tasks router
from app.services.agent_flow import run_agent_flow
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Voice Command API")

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include your API routers
app.include_router(voice.router)
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])  # Add tasks router

@app.post("/agent")
async def agent_endpoint(request: Request):
    body = await request.json()
    user_query = body.get("user_query")
    if not user_query:
        raise HTTPException(status_code=400, detail="user_query is required")
    return run_agent_flow(user_query)
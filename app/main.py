from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import voice, tasks, goals, time_session, scoreboard
from app.services.agent_flow import run_agent_flow
from app.database.base import Base
from app.database.session import engine
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Voice Command API")

# Create the database tables
Base.metadata.create_all(bind=engine)

# API Routers - These should come before the SPA catch-all route
app.include_router(voice.router, prefix="/voice")
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(goals.router, prefix="/goals", tags=["goals"])
app.include_router(time_session.router, prefix="/time_sessions")
app.include_router(scoreboard.router, prefix="/scoreboard", tags=["scoreboard"])

# Agent endpoint
@app.post("/agent")
async def agent_endpoint(request: Request):
    body = await request.json()
    user_query = body.get("user_query")
    if not user_query:
        raise HTTPException(status_code=400, detail="user_query is required")
    return run_agent_flow(user_query)

# Serve Vite React App (static files and index.html for client-side routing)
# Mount static assets from the dist folder first
app.mount("/assets", StaticFiles(directory="static/ui/dist/assets"), name="vite-assets")

# Serve index.html for all other non-API, non-file routes
@app.get("/{full_path:path}")
async def serve_react_app(request: Request, full_path: str):
    # This will serve index.html from static/ui/dist for any path not caught by API routes or specific static files.
    # React Router will then handle the specific route on the client side.
    # Ensure that your Vite build output is in 'static/ui/dist' and contains an 'index.html'
    # and that its assets (JS, CSS) are correctly linked within that index.html (Vite handles this).
    dist_path = "static/ui/dist/index.html"
    if os.path.exists(dist_path):
        return FileResponse(dist_path)
    else:
        # Fallback or could raise a 404 if index.html is crucial and not found
        raise HTTPException(status_code=404, detail="React app not found. Ensure it has been built.")

# If you had other specific static files outside the Vite app to serve (e.g. /favicon.ico from a root static folder)
# you would mount them specifically before the catch-all.
# For example: app.mount("/other_static", StaticFiles(directory="some_other_static_folder"), name="other_static")
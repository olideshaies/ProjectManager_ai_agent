import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.routers.tasks import router as tasks_router


app = FastAPI()
app.include_router(tasks_router, prefix="/api", tags=["tasks"])

@app.get("/")
def home():
    return {"message": "API is up and running!"}

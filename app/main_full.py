# app/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import Optional
from pydantic import BaseModel
import uvicorn

from app.services.transcription import transcribe_file
from app.services.agent import agent_step
from app.services.voice_capture import listen_for_audio

app = FastAPI()

class AgentResponse(BaseModel):
    text: str
    error: Optional[str] = None

@app.post("/listen", response_model=AgentResponse)
def listen_endpoint():
    """
    If server has a mic, blocks 3s, transcribe, pass to agent.
    """
    try:
        user_query = listen_for_audio(duration_seconds=3)
        response = agent_step(user_query)
        return AgentResponse(text=response)
    except Exception as e:
        return AgentResponse(text="", error=str(e))

@app.post("/voice", response_model=AgentResponse)
async def voice_upload(audio_file: UploadFile = File(...)):
    """
    Client uploads an audio file.
    """
    try:
        file_location = "/tmp/temp.wav"
        with open(file_location, "wb") as f:
            f.write(await audio_file.read())
        user_query = transcribe_file(file_location)
        agent_response = agent_step(user_query)
        return AgentResponse(text=agent_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from app.services.voice_capture import transcribe_audio
from app.services.agent import agent_step

router = APIRouter()

@router.post("/voice/command")
async def voice_command(audio_file: UploadFile = File(...)):
    temp_file = "temp_input_audio.wav"
    try:
        with open(temp_file, "wb") as f:
            shutil.copyfileobj(audio_file.file, f)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Detailed error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}\nDetails: {error_details}")
    finally:
        audio_file.file.close()
    
    transcription = transcribe_audio(temp_file)
    # Format the input as a conversation message
    conversation_messages = [{"role": "user", "content": transcription}]
    response_message = agent_step(conversation_messages)
    os.remove(temp_file)
    
    return {"transcription": transcription, "message": response_message}

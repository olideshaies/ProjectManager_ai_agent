import pyaudio
import numpy as np
import whisper
import wave
import logging
import time
from dotenv import load_dotenv
import os
load_dotenv()

from app.services.synthesizer import Synthesizer  # Adjust the import based on your structure
from app.database.vector_store import VectorStore
import pandas as pd


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Load Whisper model (use "base" or another model)
whisper_model = whisper.load_model("base")

# Audio Stream Configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1        # Mono audio
RATE = 16000        # 16 kHz for Whisper
CHUNK = 4096        # Buffer size
DEVICE_INDEX = 2    # Adjust this index for your microphone



def listen_for_audio(duration_seconds: int = 3) -> str:
    # Initialize PyAudio
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        input=True, input_device_index=DEVICE_INDEX,
                        frames_per_buffer=CHUNK)
    logger.info("Listening for audio...")
    frames = []
    # Collect enough frames for the specified duration
    num_frames = int(RATE / CHUNK * duration_seconds)
    for _ in range(num_frames):
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
        except OSError as e:
            logger.warning(f"Warning during audio capture: {e}")
            continue
        frames.append(data)
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save to a temporary WAV file for Whisper processing
    temp_wav = "temp_audio.wav"
    with wave.open(temp_wav, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    # Use Whisper to transcribe the audio file
    result = whisper_model.transcribe(temp_wav)
    transcribed_text = result["text"].strip()
    logger.info(f"Transcribed Text: {transcribed_text}")
    return transcribed_text

def transcribe_audio(file_path: str) -> str:
    """
    Transcribes the audio file at the given file path using Whisper.
    """
    result = whisper_model.transcribe(file_path)
    transcribed_text = result["text"].strip()
    logger.info(f"Transcribed Text from file '{file_path}': {transcribed_text}")
    return transcribed_text


def prepare_context_for_synthesizer(df: pd.DataFrame) -> pd.DataFrame:
    # Rename 'contents' to 'content' if needed
    if "contents" in df.columns and "content" not in df.columns:
        df = df.rename(columns={"contents": "content"})
    
    # Create a 'category' column by extracting it from the 'metadata' dictionary
    if "metadata" in df.columns and "category" not in df.columns:
        df["category"] = df["metadata"].apply(lambda m: m.get("category") if isinstance(m, dict) else None)
    
    return df


def process_voice_command():
    """
    Captures voice input, transcribes it, and passes the text to the synthesizer.
    Then, prints or processes the synthesized response.
    """
    # Step 1: Listen and transcribe
    transcribed_text = listen_for_audio(duration_seconds=10)
    if not transcribed_text:
        logger.info("No speech detected.")
        return

    # Step 2: Pass transcribed text to the synthesizer
    # For demonstration, we assume a minimal context (or an empty DataFrame if your synthesizer requires it)
    
    vec = VectorStore()
    context = vec.search(transcribed_text, limit=3)
    logger.info(f"Context: {context}")

    synthesized_response = Synthesizer.generate_response(transcribed_text, context)
    logger.info(f"Synthesized Response: {synthesized_response.answer}")
    # Here you might interpret the synthesized response to decide if it indicates a task creation,
    # and then call your task creation API or service accordingly.

    # Play the synthesized response
    Synthesizer.play_response(synthesized_response.answer)

if __name__ == "__main__":
    try:
        while True:
            transcribed_text = listen_for_audio(duration_seconds=10)
            print(transcribed_text)

            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping voice command processing.")

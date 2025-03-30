import whisper

whisper_model = whisper.load_model("base")  

def transcribe_file(filepath: str) -> str:
    result = whisper_model.transcribe(filepath)
    return result["text"].strip()

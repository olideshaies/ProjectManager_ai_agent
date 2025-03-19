from TTS.api import TTS
from playsound import playsound

def speak_response(response: str, output_file: str = "response_output.wav", model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"):
    """
    Synthesizes speech from the provided response text and plays the audio.

    Args:
        response (str): The text to synthesize.
        output_file (str, optional): The filename to store the synthesized audio.
        model_name (str, optional): The pre-trained TTS model to use.
    """
    # Initialize the TTS engine with the specified model.
    tts = TTS(model_name=model_name)
    
    # Generate speech from the text and save it to output_file.
    tts.tts_to_file(text=response, file_path=output_file)
    print(f"Audio file generated: {output_file}")
    
    # Play the generated audio file.
    playsound(output_file)

# Example usage:
if __name__ == "__main__":
    response_text = (
        "You need to finalize the project design documents by next Tuesday, "
        "March 25, 2025, at 2:00 PM."
    )
    speak_response(response_text)

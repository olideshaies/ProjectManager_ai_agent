# tests/test_voice_capture.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.voice_capture import listen_for_audio

@patch("app.services.voice_capture.whisper_model")
@patch("app.services.voice_capture.pyaudio.PyAudio")
def test_listen_for_audio(mock_pyaudio, mock_whisper):
    # Set up the mocks for PyAudio
    fake_audio = MagicMock()
    fake_stream = MagicMock()
    fake_audio.open.return_value = fake_stream
    # Set a valid sample width (e.g., 2 bytes for 16-bit audio)
    fake_audio.get_sample_size.return_value = 2

    # Simulate frames being read
    fake_stream.read.return_value = b"fake_audio_data"
    mock_pyaudio.return_value = fake_audio

    # Set up the Whisper mock to return a fake transcription
    mock_whisper.transcribe.return_value = {"text": "Test transcription"}

    # Call the function (using a very short duration to keep the test fast)
    text = listen_for_audio(duration_seconds=1)
    assert text == "Test transcription"

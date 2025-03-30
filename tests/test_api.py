# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

client = TestClient(app)

@patch("app.routers.voice.listen_for_audio", return_value="Mock transcription")
def test_voice_upload_endpoint(mock_listen):
    # If you have a sample file, make sure the path is correct
    with open("/Users/olivierdeshaies/Documents/ai-cookbook-rag/ProjectManager_ai_agent/app/test/temp_audio.wav", "rb") as f:
        response = client.post(
            "/voice/upload",
            files={"audio_file": ("test_audio.wav", f, "audio/wav")}
        )
    assert response.status_code == 200
    json_data = response.json()
    # Check that the endpoint returns the mocked transcription
    assert json_data["text"] == "Mock transcription"

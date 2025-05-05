from fastapi.testclient import TestClient
import sys

sys.path.append("..")

from app.backend.main import app
from app.frontend.config import BackendInfo

backend_config = BackendInfo()

# Create an instance of the TestClient
client = TestClient(app)


def test_ask_agent_success():
    """
    Test the /ask_agent endpoint with a valid request
    """
    payload = {"current_user_prompt": "Hi, agent!", "chat_history": "[]"}

    backend_url = backend_config.BASE_URL + backend_config.AGENT_REQUEST_ENDPOINT
    response = client.post(backend_url, json=payload)

    assert response.status_code == 200
    assert "current_history" in response.json().keys()
    assert "agent_response" in response.json().keys()

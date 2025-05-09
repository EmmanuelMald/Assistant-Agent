from fastapi.testclient import TestClient
from fastapi import status
import uuid
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


###################### /add_user endpoint ##############################


def test_add_user_success():
    """
    Test successful user registration.
    """
    unique_email = f"testuser_{uuid.uuid4()}@example.com"
    user_payload = {
        "email": unique_email,
        "password": "aSecurePassword123",
        "full_name": "Testing User",
    }

    response = client.post("/add_user", json=user_payload)

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert "user_id" in response_data
    assert isinstance(response_data["user_id"], str)
    assert response_data["message"] == "User registered successfully!"
    assert "Location" in response.headers
    assert f"/users/{response_data['user_id']}" in response.headers["Location"]


def test_add_user_conflict_email_already_registered():
    """
    Test attempting to register a user with an email that already exists.
    """
    # testing email and password
    existing_user_email = "testinguser@examplemail.com"  # already exists
    user_payload = {"email": existing_user_email, "password": "SecurePassword123"}

    response = client.post("/add_user", json=user_payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "detail" in response_data
    assert "The email is already registered" in response_data["detail"]


def test_add_user_invalid_email_format():
    """
    Test user registration with an invalid email format.
    Handled by the FastAPI input validation
    """
    user_payload = {"email": "notanemail", "password": "aSecurePassword123"}

    response = client.post("/add_user", json=user_payload)

    # FastAPI returns 433 Unprocessable Entity for Pydantic validation errors
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data


def test_add_user_missing_password():
    """
    Test user registration with a missing required field (e.g., password).
    Esto también debería ser manejado por la validación de Pydantic.
    """
    user_payload = {"email": f"test_missing_fields_{uuid.uuid4()}@example.com"}

    response = client.post("/add_user", json=user_payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data

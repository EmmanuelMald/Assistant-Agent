from fastapi.testclient import TestClient
from app.backend.main import app
from assistant_agent.config import APIConfig

api_config = APIConfig()

ask_agent_endpoint = api_config.AGENT_REQUEST_ENDPOINT
add_user_endpoint = api_config.CREATE_USER_ENDPOINT
login_user_endpoint = api_config.LOGIN_ENDPOINT

# Create an instance of the TestClient
client = TestClient(app)

# # Email for testing
# unique_email = f"testuser_{uuid.uuid4()}@example.com"

# async def override_get_current_user_id() -> str:
#     """
#     Return a fix test user_id without validate any token
#     """
#     return "UID00000"


# # Override dependency before making a request, needs to be another function
# app.dependency_overrides[get_current_user_id_from_token] = override_get_current_user_id


# def test_ask_agent_success():
#     """
#     Test the /ask_agent endpoint with a valid request
#     """
#     payload = {
#         "current_user_prompt": "Hi, agent!",
#         "chat_session_id": None,
#     }

#     response = client.post(ask_agent_endpoint, json=payload)

#     response_data = response.json()

#     assert response.status_code == 200
#     assert "chat_session_id" in response_data
#     assert isinstance(response_data["chat_session_id"], str)
#     assert "agent_response" in response.json().keys()


# ###################### /add_user endpoint ##############################


# def test_add_user_success():
#     """
#     Test successful user registration.
#     """

#     user_payload = {
#         "email": unique_email,
#         "password": "SecurePassword123",
#         "full_name": "Testing User",
#     }

#     response = client.post(add_user_endpoint, json=user_payload)

#     assert response.status_code == status.HTTP_201_CREATED
#     response_data = response.json()
#     assert "access_token" in response_data
#     assert "token_type" in response_data
#     assert "bearer" in response_data["token_type"]
#     assert "username" in response_data
#     assert "Location" in response.headers


# def test_add_user_conflict_email_already_registered():
#     """
#     Test attempting to register a user with an email that already exists.
#     """
#     # testing email and password
#     existing_user_email = unique_email  # already exists
#     user_payload = {
#         "email": existing_user_email,
#         "password": "SecurePassword123",
#         "full_name": "Testing User 0",
#     }

#     response = client.post(add_user_endpoint, json=user_payload)
#     response_data = response.json()
#     assert response.status_code == status.HTTP_409_CONFLICT
#     assert "detail" in response_data
#     assert "user is already registered" in response_data["detail"]


# def test_add_user_invalid_email_format():
#     """
#     Test user registration with an invalid email format.
#     Handled by the FastAPI input validation
#     """
#     user_payload = {"email": "notanemail", "password": "aSecurePassword123"}

#     response = client.post(add_user_endpoint, json=user_payload)

#     # FastAPI returns 433 Unprocessable Entity for Pydantic validation errors
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#     response_data = response.json()
#     assert "detail" in response_data


# def test_add_user_missing_password():
#     """
#     Test user registration with a missing required field (e.g., password).
#     Esto también debería ser manejado por la validación de Pydantic.
#     """
#     user_payload = {"email": f"test_missing_fields_{uuid.uuid4()}@example.com"}

#     response = client.post(add_user_endpoint, json=user_payload)

#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#     response_data = response.json()
#     assert "detail" in response_data

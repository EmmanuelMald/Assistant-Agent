from pydantic_settings import BaseSettings
from pydantic import SecretStr


# Little change
class GCPConfig(BaseSettings):
    PROJECT_ID: str = "learned-stone-454021-c8"
    DEV_SA: str = "dev-service-account@learned-stone-454021-c8.iam.gserviceaccount.com"
    BUCKET_NAME: str = "ai_agent_assistant"
    REGION: str = "northamerica-south1"
    GENAI_IMAGES_PATH: str = "genai_images/tmp"
    BQ_DATASET_ID: str = "ai_agent"
    USERS_TABLE_NAME: str = "users"
    USERS_TABLE_PK: str = "user_id"
    CHAT_SESSIONS_TABLE_NAME: str = "chat_sessions"
    CHAT_SESSIONS_TABLE_PK: str = "chat_session_id"
    PROMPTS_TABLE_NAME: str = "prompts"
    PROMPTS_TABLE_PK: str = "prompt_id"
    AGENT_STEPS_TABLE_NAME: str = "agent_steps"
    AGENT_STEPS_TABLE_PK: str = "step_id"


# check models: https://ai.google.dev/gemini-api/docs/image-generation
class LLMConfig(BaseSettings):
    SECRET_ID: str = "GEMINI-API-KEY"
    SECRET_VERSION: str = "1"
    API_KEY: SecretStr = ""
    AGENT_MODEL_NAME: str = "gemini-2.5-pro-preview-03-25"
    PROMPTING_MODEL_NAME: str = "gemini-2.5-pro-preview-03-25"
    PROMPTING_MODEL_TEMPERATURE: float = 0.05
    IMAGE_GENERATION_MODEL_NAME: str = "imagen-3.0-generate-002"
    IMAGE_GENERATION_TEMPERATURE: float = 0.8
    DEFAULT_GENERATED_IMAGES: int = 1
    AGENT_MESSAGES_MEMORY_LIMIT: int = 5


class AuthConfig(BaseSettings):
    # You can generate a random key running openssl rand -hex 32
    SECRET_KEY: SecretStr = ""
    SECRET_ID: str = "FASTAPI_SECRET_KEY"
    SECRET_VERSION: str = "1"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


class APIConfig(BaseSettings):
    BASE_URL: str = "https://agent-api-214571216460.northamerica-south1.run.app"
    AGENT_REQUEST_ENDPOINT: str = "/ask_agent"
    CREATE_USER_ENDPOINT: str = "/add_user"
    LOGIN_ENDPOINT: str = "/login"
    CHAT_SESSIONS_ENDPOINT: str = "/chat_sessions"
    CHAT_SESSION_HISTORY_ENDPOINT: str = "/chat_sessions/{chat_session_id}/history"

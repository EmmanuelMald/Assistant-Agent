from pydantic_settings import BaseSettings


class BackendInfo(BaseSettings):
    BASE_URL: str = "http://localhost:8000"
    AGENT_REQUEST_ENDPOINT: str = "/ask_agent"

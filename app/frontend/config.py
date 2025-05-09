from pydantic_settings import BaseSettings


class BackendInfo(BaseSettings):
    BASE_URL: str = "https://agent-api-214571216460.northamerica-south1.run.app"
    AGENT_REQUEST_ENDPOINT: str = "/ask_agent"
    CREATE_USER_ENDPOINT: str = "/add_user"

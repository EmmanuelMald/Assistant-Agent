from pydantic_settings import BaseSettings
from pydantic import SecretStr


class GCPConfig(BaseSettings):
    PROJECT_ID: str = "learned-stone-454021-c8"
    DEV_SA: str = "dev-service-account@learned-stone-454021-c8.iam.gserviceaccount.com"
    BUCKET_NAME: str = "rag_llm_energy_expert"
    REGION: str = "northamerica-south1"


class LLMConfig(BaseSettings):
    SECRET_ID: str = "GEMINI-API-KEY"
    SECRET_VERSION: str = "1"
    API_KEY: SecretStr = ""
    MODEL: str = "gemini-2.0-flash"
    TEMPERATURE: float = 0.05

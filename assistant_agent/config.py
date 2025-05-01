from pydantic_settings import BaseSettings
from pydantic import SecretStr


class GCPConfig(BaseSettings):
    PROJECT_ID: str = "learned-stone-454021-c8"
    DEV_SA: str = "dev-service-account@learned-stone-454021-c8.iam.gserviceaccount.com"
    BUCKET_NAME: str = "rag_llm_energy_expert"
    REGION: str = "northamerica-south1"
    GENAI_IMAGES_PATH: str = "genai_images"


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
    DEFAULT_GENERATED_IMAGES: int = 4

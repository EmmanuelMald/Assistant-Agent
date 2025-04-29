from loguru import logger
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
import sys

sys.path.append("..")
from assistant_agent.credentials import get_llm_config

llm_config = get_llm_config()

model = GeminiModel(
    llm_config.MODEL,
    provider=GoogleGLAProvider(api_key=llm_config.API_KEY.get_secret_value()),
)

agent = Agent(model)

result = agent.run_sync("Where does 'hello world' come from?")
logger.info(f"{result.output}")

from loguru import logger
from pydantic_ai import Agent, Tool
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
import sys

sys.path.append("..")

from assistant_agent.credentials import get_llm_config
from assistant_agent.tools.prompt_image_generator import generate_prompt_image

llm_config = get_llm_config()

system_prompt = "You are a specialized AI assistant, an expert prompt engineer"

model = GeminiModel(
    llm_config.MODEL,
    provider=GoogleGLAProvider(api_key=llm_config.API_KEY.get_secret_value()),
)

agent = Agent(
    model,
    tools=[
        Tool(generate_prompt_image, takes_ctx=False),
    ],
    system_prompt=system_prompt,
)


result = agent.run_sync(
    "Help me generate a prompt to generate an image"
    "to be printed in a t-shirt. The concept is 'quantum entanglement'."
)
logger.info(f"{result.output}")

from loguru import logger
from pydantic_ai import Agent, Tool
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
import sys

sys.path.append("..")

from assistant_agent.credentials import get_llm_config
from assistant_agent.tools.image_generator import generate_prompt_image, generate_image

llm_config = get_llm_config()

system_prompt = (
    "You are a specialized AI assistant capable of using different tools that helps you to generate images based on a user's idea."
    " You have access to the following tools:\n"
    "- `generate_prompt_image(idea: str)`: Generates a detailed prompt for an image generation model based on a user's idea.\n"
    "- `generate_image(prompt: str, general_image_name: str)`: Generates an image based on a given prompt and saves it to GCS.\n"
    "When a user asks for an image, first consider if you need to generate a detailed prompt using `generate_prompt_image`."
    " If you already have a suitable prompt or have just generated one, use `generate_image` to create the image."
    " Respond to the user with a description of the generated image and its GCS location."
)

model = GeminiModel(
    llm_config.AGENT_MODEL_NAME,
    provider=GoogleGLAProvider(api_key=llm_config.API_KEY.get_secret_value()),
)

agent = Agent(
    model,
    tools=[
        Tool(generate_prompt_image, takes_ctx=False),
        Tool(generate_image, takes_ctx=False),
    ],
    system_prompt=system_prompt,
)


result = agent.run_sync(
    "Generate just two images. The main idea is a technological and realistic heart"
)
logger.info(f"{result.output}")

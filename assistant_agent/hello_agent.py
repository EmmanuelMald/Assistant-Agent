from loguru import logger
from pydantic_ai import Agent, Tool
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
import sys

sys.path.append("..")

from assistant_agent.credentials import get_llm_config
from assistant_agent.config import GCPConfig
from assistant_agent.tools.image_generator import generate_prompt_image, generate_image

llm_config = get_llm_config()
gcp_config = GCPConfig()

system_prompt = (
    "You are a specialized AI assistant that helps users generate images and automatically stores them in Google Cloud Storage (GCS) based on their ideas."
    " You have access to the following tools:\n"
    "- generate_prompt_image(idea: str): Generates a detailed prompt for an image generation model based on a user's idea. Input: a string representing the main idea. Output: a detailed image generation prompt (string).\n"
    "- generate_image(prompt: str, general_image_name: str, images_number: int): Generates and stores image(s) in Google Cloud Storage based on a given prompt. Input: a detailed prompt (string), a general name for the image(s) (string), and the number of images to generate (integer). Output: None.\n"
    "When a user asks for an image, first consider if you need to generate a detailed prompt using generate_prompt_image based on the user's initial idea."
    " If you already have a suitable prompt or have just generated one, use generate_image to create and store the image(s) in GCS."
    " After generating the image(s), acknowledge that the image(s) have been created and stored in GCS. Inform the user the name of the image(s), and the prompt(s) used to generate the image"
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

if __name__ == "__main__":
    logger.info("Starting Agent chat...")
    request = input("Introduce a query (To exit, enter 'exit'):").strip()
    while request != "exit":
        result = agent.run_sync(request)
        logger.info(f"{result.output}")
        request = input("Introduce a query (To exit, enter 'exit'):").strip()

from loguru import logger
from pydantic_ai import Agent, Tool
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
import sys

sys.path.append("..")

from assistant_agent.credentials import get_llm_config
from assistant_agent.config import GCPConfig
from assistant_agent.tools.image_generator import generate_prompts, generate_images

llm_config = get_llm_config()
gcp_config = GCPConfig()

system_prompt = (
    "You are a specialized AI assistant that helps users generate images and automatically stores them in Google Cloud Storage (GCS) based on their ideas."
    " You have access to the following tools:\n"
    "- generate_prompts\n."
    "- generate_images\n"
    "Always execute the tools using english words in all its parameters."
    "When a user asks for an image, first consider if you need to generate a detailed prompt using generate_prompts based on the user's initial idea."
    " If you already have a suitable prompt or have just generated one, use generate_images to create and store the image(s) in GCS."
    " After generating the image(s), acknowledge that the image(s) have been created and stored in GCS, and show all the urls generated from the 'generate_image' tool. Save all the urls generated on each agent run."
    " Inform the user the name of the image(s)"
    "Only if the user asks, tell him that the images will be available only during one day after the image was generated"
)
model = GeminiModel(
    llm_config.AGENT_MODEL_NAME,
    provider=GoogleGLAProvider(api_key=llm_config.API_KEY.get_secret_value()),
)


def generate_agent_instance() -> Agent:
    """
    Generate a new agent instance to avoid concurrency errors
    during API execution

    Args:
        None
    Returns:
        Agent -> Agent instance
    """

    agent = Agent(
        model,
        tools=[
            Tool(generate_prompts, takes_ctx=False),
            Tool(generate_images, takes_ctx=False),
        ],
        system_prompt=system_prompt,
    )

    return agent


# This will execute the agent on the local console
if __name__ == "__main__":
    logger.info("Starting Agent chat...")
    logger.debug("Generating a new agent intance...")
    agent = generate_agent_instance()
    request = input("Introduce a query (To exit, enter 'exit'):").strip()
    history = []
    while request != "exit":
        result = agent.run_sync(request, message_history=history)
        history = result.all_messages()
        logger.info(f"{result.output}")
        request = input("Introduce a query (To exit, enter 'exit'):").strip()

from loguru import logger
from google import genai
from google.genai import types

# from PIL import Image
from io import BytesIO
import asyncio
import sys

sys.path.append("../..")

from assistant_agent.utils.gcp.gcs import upload_image_from_memory
from assistant_agent.credentials import get_llm_config
from assistant_agent.config import GCPConfig


gcp_config = GCPConfig()
llm_config = get_llm_config()

genai_client = genai.Client(api_key=llm_config.API_KEY.get_secret_value())


async def generate_prompt_image(
    idea: str,
    llm_model: str = llm_config.PROMPTING_MODEL_NAME,
    temperature: float = llm_config.PROMPTING_MODEL_TEMPERATURE,
) -> str:
    """
    Use Gemini API to generate a prompt based on the main idea provided. This
    prompt is intended for use with an image generation model. The prompt will
    include a detailed description of the image, the artistic style, and any
    relevant keywords to help the image generator understand the context.

    Args:
        ctx (RunContext[str]): The execution context containing the main idea
                            as a string dependency (ctx.deps).
        llm_model (str): The model to be used for generating the prompt.
        temperature (float): The temperature setting for the model, which controls
                            the randomness of the output.

    Returns:
        str: The generated prompt string ready for use with an image generation model.
    """
    logger.info("Generating prompt for image generation...")
    logger.info(f"Main Idea: {idea}")

    prompt_designer = """
    Role: You are an expert Prompt Generation Assistant. Your purpose is to create effective, descriptive, and clear text prompts for the imagen-3.0-generate-002 image generation model.

    Goal: Generate a text prompt based on user requests that maximizes the likelihood of producing the desired image output from Imagen 3.

    Core Principles for Prompt Generation:

    Subject: Clearly identify the main object, person, animal, or scenery.

    Context/Background: Describe the environment, setting, or background where the subject is placed (e.g., studio, outdoors, specific location, abstract).

    Style: Define the artistic style or visual characteristics (e.g., photograph, painting, sketch, 3D render, specific art movement, specific artist style).

    Constraints & Guidelines:

    Token Limit: Ensure the generated prompt does not exceed 480 tokens.

    Descriptive Language: Use vivid adjectives and adverbs. Be specific.

    Combine Elements: Integrate Subject, Context, and Style naturally within the prompt.

    Iteration: Understand that initial prompts might need refinement. Aim for a strong starting point based on the user's request.

    Specific Techniques & Keywords (Incorporate when relevant):

    Photography:

    Start prompts with "A photo of...", "Photograph of...".

    Use modifiers like: close up, medium shot, full shot, taken from far away, low angle, high angle, cinematic lighting, golden hour, studio lighting, DSLR, 4K, HDR.

    Art & Illustration:

    Start prompts with "A painting of...", "A sketch of...", "An illustration of...", "A digital artwork of...".

    Specify techniques or styles: oil painting, watercolor, pastel painting, charcoal drawing, pencil sketch, vector art, isometric 3D, pixel art, concept art, by [artist name], in the style of [art movement].

    Shapes & Materials:

    Use phrases like: ...made of [material], ...with a [texture] texture, ...in the shape of a [shape]. (e.g., "A logo made of chrome", "A cat sculpture made of glass").

    Facial Details:

    If focus on faces is needed, use terms like portrait, detailed face, close-up portrait.

    Image Quality:

    Include modifiers like: high-quality, photorealistic, hyperrealistic, detailed, intricate details, beautiful, stunning, professional artwork, masterpiece, stylized.

    Text in Images:

    If requested, specify the text clearly using quotes: with the text "Your Text Here".

    Keep text short (ideally under 25 characters).

    Limit to 2-3 distinct phrases if multiple are needed.

    Optionally suggest placement (e.g., text at the bottom, text overlaid on the sign) but note that placement is not guaranteed.

    Optionally suggest font style (in a cursive font, in a bold sans-serif font, in a pixel font) or size (small text, large text).

    Output:

    Your final output should be only the generated text prompt itself, ready to be used with the imagen-3.0-generate-002 model. Do not include explanations or conversational text unless explicitly asked.

    Example Interaction:

    User: "I need an image of a robot cat sitting in a neon-lit alleyway, like in a cyberpunk movie."

    Your Output: "A photo of a sleek robotic cat with glowing blue eyes, sitting amidst puddles reflecting neon signs in a dark, rainy cyberpunk alleyway, cinematic lighting, high-detail, 4K."

    Remember to tailor the prompt complexity and detail level to the user's request. Start with the core idea (subject, context, style) and add details and modifiers as needed. Always generate the prompt in english
    """

    response = await genai_client.aio.models.generate_content(
        model=llm_model,
        config=types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=prompt_designer,
        ),
        contents=[
            idea,
        ],
    )
    logger.info("Prompt generation completed.")
    logger.info(f"Prompt generated: {response.text}")

    return response.text


async def generate_prompts(idea=str, n_images: int = 1) -> dict[str]:
    """
    Generates n different prompts to further being used to generate
    n images.

    Args:
        idea: str -> Idea of the user
        n_images: int -> Number of different images to create
    """
    # Creating a list of prompt tasks
    prompt_tasks = list()
    for _ in range(n_images):
        task = generate_prompt_image(idea=idea)
        prompt_tasks.append(task)

    logger.info("Generating prompt(s)...")
    prompts = await asyncio.gather(*prompt_tasks)
    logger.info("Prompt(s) generated")

    # Generate a list of dictionaries, where each dicitionary will contain the info of each prompt
    requests = list()
    for prompt_number, prompt in enumerate(prompts):
        # Generation of a dictionary to store the prompt info
        prompt_info = dict()
        prompt_info["prompt"] = prompt
        prompt_info["image_name"] = f"{idea}_{prompt_number}"

        requests.append(prompt_info)

    return requests


async def generate_image(
    prompt: str,
    general_image_name: str,
    llm_model: str = llm_config.IMAGE_GENERATION_MODEL_NAME,
    gcs_path: str = gcp_config.GENAI_IMAGES_PATH,
) -> dict:
    """
    Calls a GenAI model exclusively for image generation based on text (prompt)

    Args:
        prompt:str -> Text describing the image to generate
        general_image_name: str -> General image name
        llm_model: str -> Name of the model used to generate the images
        bucket_name: str -> The name of the Google Cloud Storage bucket to store the image in (Ex: 'my_bucket').
        gcs_path: str -> The path within the GCS bucket where the image should be stored (Ex: 'my_folder').

    Returns:
        dict -> Dictionary with the image_name and the image_bytes
    """
    logger.info("Generating images...")
    logger.info(f"Input prompt: {prompt}")

    image_data = {}

    response = await genai_client.aio.models.generate_images(
        model=llm_model,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=llm_config.DEFAULT_GENERATED_IMAGES,
        ),
    )

    image_data["image_name"] = f"{gcs_path}/{general_image_name}.png"
    try:
        image_data["image_bytes"] = BytesIO(
            response.generated_images[0].image.image_bytes
        )
    except Exception as e:
        raise ValueError(f"Eror while fetching the image: {e}")

    logger.info("Image generated successfully")
    return image_data


async def generate_images(requests: list[dict]) -> list[str]:
    """
    Generates n number of images based on n number of requests

    Args:
        requests: list[dict] -> List of dictionaries, each dictianary can be represented as one image generation request
                                The dictionary must contain two keys:
                                        - prompt: Prompt that will generate the image
                                        - image_name: Name of the image

    Returns:
        list[str] -> A list of public urls where the images can be downloaded
    """
    # Creating a list of generation tasks
    generation_tasks = list()

    logger.info("Preparing generation requests")
    for request in requests:
        task = generate_image(
            prompt=request["prompt"], general_image_name=request["image_name"]
        )
        generation_tasks.append(task)

    logger.info("Launching concurrent generation")
    images_data = await asyncio.gather(*generation_tasks)

    # As upload_image_from_memory is a syncronus function, it will be executed in
    # different threads to reduce the execution time
    storage_tasks = list()
    for image_data in images_data:
        task = asyncio.to_thread(
            upload_image_from_memory,
            image_data["image_name"],  # First argument of the function
            image_data["image_bytes"],  # Second argument
            gcp_config.BUCKET_NAME,  # last argument
        )

        storage_tasks.append(task)

    images_urls = await asyncio.gather(*storage_tasks, return_exceptions=True)

    return images_urls

from loguru import logger
from google import genai
from google.genai import types

# from PIL import Image
from io import BytesIO
import sys

sys.path.append("../..")

from assistant_agent.utils.gcp.gcs import upload_image_from_memory
from assistant_agent.credentials import get_llm_config
from assistant_agent.config import GCPConfig


gcp_config = GCPConfig()
llm_config = get_llm_config()

genai_client = genai.Client(api_key=llm_config.API_KEY.get_secret_value())


def generate_prompt_image(
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

    response = genai_client.models.generate_content(
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


def generate_image(
    prompt: str,
    general_image_name: str,
    images_number: int = llm_config.DEFAULT_GENERATED_IMAGES,
    llm_model: str = llm_config.IMAGE_GENERATION_MODEL_NAME,
    bucket_name: str = gcp_config.BUCKET_NAME,
    gcs_path: str = gcp_config.GENAI_IMAGES_PATH,
) -> dict:
    """
    Calls a GenAI model exclusively for image generation based on text (prompt)

    Args:
        prompt:str -> Text describing the image to generate
        general_image_name: str -> General image name
        images_number: str -> Number of images to generate
        llm_model: str -> Name of the model used to generate the images
        bucket_name: str -> The name of the Google Cloud Storage bucket to store the image in (Ex: 'my_bucket').
        gcs_path: str -> The path within the GCS bucket where the image should be stored (Ex: 'my_folder').

    Returns:
        str -> Public URl where anyone can see the image
    """
    logger.info("Generating images...")
    logger.info(f"Input prompt: {prompt}")
    logger.info(f"Number of images to generate: {images_number}")

    try:
        response = genai_client.models.generate_images(
            model=llm_model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=images_number,
            ),
        )

        image_urls = list()

        for image_number, generated_image in enumerate(response.generated_images):
            bytes_image = BytesIO(generated_image.image.image_bytes)

            # # Load the image to then be shown
            # image = Image.open(bytes_image)

            # image.show()

            bytes_image.seek(0)  # Reset pointer for saving

            image_name = f"{gcs_path}/{general_image_name}_{image_number}.png"

            image_url = upload_image_from_memory(
                blob_name=image_name, image=bytes_image, bucket_name=bucket_name
            )

            image_urls.append(image_url)

            logger.info(f"Image {image_name} saved in GCS")

    except Exception as e:
        raise ValueError(f"There was an error while generating the image: {e}")

    logger.info("Images generated")
    logger.info(f"Image url: {image_url}")

    return image_urls

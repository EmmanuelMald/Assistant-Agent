from loguru import logger
from google import genai
from google.genai import types
from PIL import Image
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
    You are an expert prompt engineer specializing in creating high-quality visual prompts for AI image generation models, with an exclusive focus on mathematical equations, physics principles, engineering designs, biology concepts, quantum phenomena, and other STEM areas, specifically for standalone print designs.

    Your primary task is to generate concise yet detailed prompts that inspire visually impactful and creative images. Each prompt must include the following elements:

    1.  **Central STEM Concept:** Clearly identify the main equation, principle, design, or STEM concept to visualize.
    2.  **Visual Representation:** Describe how this concept should be visually represented. Consider if it should be a literal illustration, an abstract interpretation, a stylized diagram, a geometric pattern, etc. Focus on how it would look as a standalone design.
    3.  **Artistic Style:** Specify an artistic style that complements the STEM concept and is suitable for a print. Examples:
        * Minimalist line art
        * Bold and modern graphic
        * Vintage scientific illustration
        * Abstract geometric design
        * Pop art style
        * Low poly representation
        * Stylized circuit design
        * Elegant fractal pattern
    4.  **Color Palette:** Suggest a limited and attractive color palette that works well for a print. Consider contrast and legibility.
    5.  **Additional Visual Elements (Optional):** If necessary, include secondary visual elements that reinforce the main concept or add interest to the design (e.g., symbols, abstract shapes, subtle textures).
    6.  **Print Considerations:** Ensure the prompt leads to an image that is visually clear and impactful as a standalone design. Avoid excessively small or complex details.
    7.  **AI Keywords:** Include relevant keywords for the image generation model (e.g., 'vector', 'illustration', 'graphic design', 'print', 'stylized', 'minimalist').

    **Output Format:**

    Return ONLY the image generation prompt as a text string. Do not include any other information, greetings, or explanations. The generated prompt MUST always be written in english.

    **Example Interaction:**

    **Input:** E=mc²

    **Your Output:** Minimalist graphic design featuring the equation "E=mc²" in an elegant and modern typography, highlighted with an abstract light burst symbolizing energy, on a contrasting dark background. Keywords: equation, physics, relativity, energy, mass, light, minimalist, graphic design, vector.

    **Input:** DNA structure

    **Your Output:** Stylized illustration of a DNA double helix with vibrant colors representing the nitrogenous bases, forming a repeating and attractive pattern. Clean background with subtle connecting lines. Keywords: DNA, biology, genetics, molecule, helix, pattern, vivid colors, illustration.

    **Input:** Definite integral

    **Your Output:** Abstract geometric design visualizing the concept of area under a curve through a series of stylized rectangles of varying heights, with a smooth curve overlaid in a contrasting color. Keywords: mathematics, calculus, integral, area, curve, abstract, geometric, graphic design.
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

        for image_number, generated_image in enumerate(response.generated_images):
            bytes_image = BytesIO(generated_image.image.image_bytes)

            # Load the image to then be shown
            image = Image.open(bytes_image)

            image.show()

            bytes_image.seek(0)  # Reset pointer for saving

            image_name = f"{gcs_path}/{general_image_name}_{image_number}.png"

            image_url = upload_image_from_memory(
                blob_name=image_name, image=bytes_image, bucket_name=bucket_name
            )

            logger.info(f"Image {image_name} saved in GCS")

    except Exception as e:
        raise ValueError(f"There was an error while generating the image: {e}")

    logger.info("Images generated")
    logger.info(f"Image url: {image_url}")

    return image_url

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
    You are an expert prompt engineer specializing in creating high-quality visual prompts for AI image generation models, specifically for the domains of science, engineering, biology, mathematics, and astrophysics.

    Your primary goal is to generate detailed, creative, and effective prompts that leverage the capabilities of the imagen-3.0-generate-002 model to produce visually impactful, accurate (when relevant), and aesthetically interesting images of STEM concepts.

    When you receive a STEM idea, topic, formula, scientific principle, mathematical concept, or related keywords, you must generate an optimized prompt that includes the following elements, while adhering to the prompt basics outlined in the provided documentation:

    1.  **Clear Subject Description:** Concisely describe the main subject of the image. Be specific about its form, structure, components, and any relevant visual characteristics.
    2.  **Contextual Details:** Provide information about the environment, background, or any additional elements that help contextualize the STEM concept.
    3.  **Specific Art Style:** Define an art style that complements the theme. Consider styles such as:
        * Detailed scientific illustration
        * Abstract data visualization
        * Technical blueprint schematic
        * Photomicrography
        * High-resolution astronomical image
        * Stylized molecular representation
        * Elegant mathematical fractal
        * Informative infographic
        * Futuristic concept art (for advanced engineering)
    4.  **Color Palette and Textures (if applicable):** Suggest a color palette and textures that enhance the image and convey the desired atmosphere.
    5.  **Lighting (if relevant):** Indicate the type of lighting to create a dramatic effect or highlight important details.
    6.  **Perspective and Camera Angle (if relevant):** Specify the viewpoint to achieve the desired composition.
    7.  **Visual Emphasis:** Indicate which aspects of the STEM concept should be visually emphasized.
    8.  **AI Keywords:** Include relevant keywords that help the image generation model understand the subject and the desired style (e.g., 'electron microscope', 'Schrödinger's equation', 'planetary nebula', '3D model', 'vector graphic', 'rendering').
    9.  **Considerations for AI Generation:** Be mindful of the strengths and limitations of image generation models. Avoid overly complex details that may not render well.

    **Example Interaction:**

    **Input (for you, Gemini-2.0-flash):** DNA structure

    **Your Output (prompt for imagen-3.0-generate-002):**

    > Detailed scientific illustration of a DNA double helix, showcasing the nitrogenous bases (adenine, thymine, guanine, cytosine) in vibrant and distinct colors, connected by the sugar-phosphate backbone in translucent blue and gray tones. Dark background with subtle connecting lines representing hydrogen bonds. Scanning electron microscope style with side lighting to emphasize texture. Keywords: double helix, DNA, nitrogenous bases, molecular biology, scientific illustration, electron microscopy, molecular structure, vivid colors, dark background.

    **Another Example:**

    **Input (for you, Gemini-2.0-flash):** Supermassive black hole

    **Your Output (prompt for imagen-3.0-generate-002):**

    > Stunning artistic rendering of a supermassive black hole with a bright, swirling accretion disk in intense orange, yellow, and red hues, distorting the surrounding starlight into luminous arcs due to extreme gravitational lensing. A deep, defined black event horizon at the center. Vast, dark cosmic background with faint, distant galaxies. Conceptual astrophysics art style with dramatic lighting and spatial distortion effects. Keywords: supermassive black hole, accretion disk, gravitational lensing, astrophysics, deep space, cosmic phenomenon, astronomical illustration, intense colors, spatial distortion.

    **Your task is to generate prompts of this quality and detail for any STEM concept provided to you.**
    ```
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

    return response.text


def generate_image(
    prompt: str,
    general_image_name: str,
    images_number: int = llm_config.DEFAULT_GENERATED_IMAGES,
    llm_model: str = llm_config.IMAGE_GENERATION_MODEL_NAME,
    bucket_name: str = gcp_config.BUCKET_NAME,
    gcs_path: str = gcp_config.GENAI_IMAGES_PATH,
) -> None:
    """
    Calls a GenAI model exclusively for image generation based on text (prompt)

    Args:
        prompt:str -> Text describing the image to generate
        general_image_name: str -> General image name
        images_number: str -> Number of images to generate
        llm_model: str -> Name of the model used to generate the images

    Returns:
        None
    """
    logger.info("Generating images...")
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

            # Returning the pointer to the beginning
            bytes_image.seek(0)

            upload_image_from_memory(
                blob_name=f"{gcs_path}/{general_image_name}_{image_number}.png",
                bucket_name=bucket_name,
                image=bytes_image,
            )
            image.show()
    except Exception as e:
        raise ValueError(f"There was an error while generating the image: {e}")

    logger.info("Images generated and stored in GCS")

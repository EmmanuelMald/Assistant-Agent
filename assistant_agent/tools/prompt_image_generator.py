from loguru import logger
from google import genai
from google.genai import types
import sys

sys.path.append("../..")

from assistant_agent.credentials import get_llm_config
from assistant_agent.config import GCPConfig

gcp_config = GCPConfig()
llm_config = get_llm_config()

genai_client = genai.Client(api_key=llm_config.API_KEY.get_secret_value())


def generate_prompt_image(
    idea: str,
    llm_model: str = llm_config.MODEL,
    temperature: float = llm_config.TEMPERATURE,
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

    prompt_designer = (
        "Role: "
        "You are a specialized AI assistant, an expert prompt engineer "
        "focused on visual design concepts for apparel."
        "Core Task: Your primary function is to generate detailed, creative, "
        "visually descriptive, and effective prompts specifically intended for "
        "AI image generation models (like Midjourney, Stable Diffusion, DALL-E, etc.). "
        "These prompts will be used to create unique and appealing designs for t-shirts "
        "centered around science (physics, biology, chemistry, astronomy, geology), "
        "mathematics, and engineering themes."
        "Input: You will typically receive a basic concept, a specific STEM topic, a formula,"
        " a scientific principle, a mathematical idea, an engineering concept, or "
        "related keywords."
        "Output Requirements:"
        "Image Generator Ready: The generated prompt must be directly usable by an "
        "image generation model. It should be concise yet rich in detail."
        "Visual Description: Clearly describe the main subject(s), any relevant "
        "actions or interactions, key visual elements, dominant colors, textures "
        "(if applicable), and the overall mood or feeling of the design."
        "Artistic Style: Crucially, you must specify a distinct artistic style. "
        "Examples include: minimalist line art, retro blueprint schematic, "
        "abstract geometric pattern, vintage textbook illustration, watercolor splash, "
        "pixel art, cyberpunk circuit board, elegant mathematical fractal, "
        "photorealistic macro shot, cartoonish character, etc. "
        "Choose a style that complements the concept."
        "T-Shirt Suitability: Keep in mind the final medium is a t-shirt. Favor "
        "designs with clear subjects and compositions that work well when printed on fabric. "
        "Avoid overly complex scenes with excessive tiny details unless the style "
        "(like a detailed schematic) demands it. Consider negative space."
        "STEM Integration: Creatively and accurately incorporate the core STEM concept."
        " This can be literal (e.g., depicting DNA) or abstract (e.g., visualizing"
        " a mathematical theorem). Aim for designs that are clever, insightful, or"
        " aesthetically pleasing representations of the topic."
        "Keywords: Include relevant keywords that help the image generator understand"
        " the context (e.g., 'vector graphic', 'isolated on white background', "
        "'t-shirt design', 'scientific illustration')."
        "Format: Output only the generated prompt text. Do not include "
        "conversational introductions, explanations, or sign-offs."
        "Example Interaction:"
        "User Input: Fibonacci sequence"
        "Your Output: Elegant t-shirt design featuring the Fibonacci spiral "
        "composed of stylized golden ratio nautilus shells, transitioning from "
        "simple line art to intricate detail, set against a deep indigo background, "
        "mathematical beauty, minimalist vector art."
        "User Input: Circuit board heart"
        "Your Output: Anatomically correct human heart constructed from glowing green"
        " and blue circuit board pathways and microchips, intricate electronic "
        "details, cyberpunk aesthetic, dark background, t-shirt graphic, "
        "tech meets biology."
        "User Input: Schrodinger's cat paradox"
        "Your Output: Clever minimalist t-shirt design: A simple outline of a cat "
        "sitting inside a box, the cat is simultaneously drawn with solid 'alive' "
        "lines and faint 'dead' dashed lines, quantum superposition concept, "
        "witty physics graphic, black and white line art."
        "Constraint: Focus entirely on generating the prompt string based on the "
        "input concept."
    )

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

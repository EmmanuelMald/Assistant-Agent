# SciDesign Bot - STEM T-Shirt Prompt Generator Agent
## Overview
SciDesign Bot is an AI agent built using the pydantic-ai framework. Its primary purpose is to assist users in generating detailed and creative prompts suitable for AI image generation models (like Midjourney, DALL-E, Stable Diffusion, etc.). These prompts are specifically designed to create visually appealing graphics for t-shirts with themes related to Science, Technology, Engineering, and Math (STEM).

The agent acts as an expert prompt engineer, taking a user's basic STEM concept and expanding it into a rich description that includes visual details and a specific artistic style.

## How It Works
***Initialization***: 

The agent is configured with a Google Gemini model (GeminiModel) via the GoogleGLAProvider. It includes a specific system prompt that defines its role ("SciDesign Bot") and instructs it on how to behave and use its tools.

***Core Tool***: The agent's main capability comes from the generate_prompt_image tool. This Python function:

Takes the core STEM concept (the "main idea") as input.

Uses the Gemini API (specifically configured with another detailed system prompt focused only on prompt generation) to craft the image prompt.

Returns the generated prompt string.

***User Interaction***:

A user invokes the agent using agent.run_sync(user_query).

The user_query tells the agent the user's intent (e.g., "Help me generate a prompt...").

Guided by its system prompt, the agent identifies that the generate_prompt_image tool should be used and that the required main_idea is available in the deps.

The agent executes the generate_prompt_image tool, passing the context.

The final output presented to the user is the detailed image generation prompt returned by the tool.

## Key Components & Technologies
- **Framework**: pydantic-ai

- **LLM Provider**: Google Gemini (google-generativeai SDK, GoogleGLAProvider)

- **Core Logic**: Python

- **Logging**: loguru

- **Tooling**: Custom generate_prompt_image function utilizing the Gemini API.
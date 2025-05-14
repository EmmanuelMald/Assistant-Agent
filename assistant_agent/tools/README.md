# Tools

A tool is a mechanism for LLMs (Large Language Models) to retrieve extra information to help them generate a response. 

In this case, the project contains only two Tools which are stored in the image_generator script. Allowing to add new tools that might not be related to the image generation.

## Prompt for Image Generation Tool

This tool takes one idea or ideas of the user, even the most basic one such as 'summer', and generate a more complex/suited prompt that then the **Image Generation Tool** will take to produce an image. 

This tool allows the agent to generate more than one specialized prompt at the time, each one with different ideas; Also, it allows the user to ask for images in simple words.

## Image Generation Tool

This tool is capable of generate N amount of images based on the prompts provided by the agent, it does not require the prompts to be similar.

When the images are generated, automatically are stored into GCS (Google Cloud Storage), returning the link to its images.

## 

**Both tools are capable of use parallelization to generate N promts/images at once**



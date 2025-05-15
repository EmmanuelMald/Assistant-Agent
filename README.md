# AI Agent - Image Generator

## Overview

This AI Agent was built to address two of the main problems when a user tries to generate an image with AI:

- Generating the right prompt to get what the user wants

- Generate more than one image per user request (if asked to), which can also be of different topics each.

Is capable of generate different images with different styles, but is mainly focus on generate realistic images.

This agent is deployed in [**Google Cloud Platform**](https://cloud.google.com/?hl=en), so you can test it by just register for free [**here**](https://agent-app-214571216460.northamerica-south1.run.app) - *The images, once generated, will be deleted after 7 days.*

## Key Components and Technologies

The AI Agent was built using the [**PydanticAI**](https://ai.pydantic.dev/) agent framework, and some of the [**Gemini**](https://gemini.google.com/app) models, mainly [**Gemini 2.5 Pro**](https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-pro) and [**Imagen 3**](https://ai.google.dev/gemini-api/docs/imagen).

The Cloud infrastructure was developed using [**Terraform**](https://developer.hashicorp.com/terraform) and deployed through *CICD* pipelines with [**CloudBuild**](https://cloud.google.com/build?hl=en).

The app was containerized using [**Docker**](https://www.docker.com/) and deployed on two serverless instances on [**CloudRun**](https://cloud.google.com/run?hl=en):


- One related to the API that contains all the logic of the AI Agent (built with [**FastAPI**](https://fastapi.tiangolo.com/) and secured using [**JWT**](https://jwt.io/introduction)).

- Other related to the frontend section (built with [**Streamlit**](https://streamlit.io/)).

All the chat sessions data are stored on [**BigQuery**](https://cloud.google.com/bigquery?hl=en), whereas the generated images are stored in [**Google Cloud Storage**](https://cloud.google.com/storage?hl=en) buckets - which are automatically deleted after 7 days.

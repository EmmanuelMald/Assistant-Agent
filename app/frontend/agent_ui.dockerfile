# Pull a Python image
FROM python:3.11-slim-bullseye

ENV UV_VERSION=0.5.4

# Create the main directoy where everything will be stored
WORKDIR /Assistant-Agent

# Copy pyproject.toml and uv.lock in the working directory
COPY pyproject.toml uv.lock ./

# Upgrade pip and install the required uv version
RUN pip install --upgrade pip &&\
    pip install uv==${UV_VERSION}

# Create a requirements.txt from the pyproject.toml
RUN uv export --group agent_ui --no-hashes -o requirements.txt

RUN pip install --no-cache-dir -r requirements.txt 

# Copying all the necessary
COPY app/frontend/. ./app/frontend/

# Move to the app directory to execute uvicorn without errors
WORKDIR /Assistant-Agent/app/frontend/

# Expose the port where the app will listen
EXPOSE 8501

# Execute the app
CMD ["streamlit", "run", "agent_ui.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.headless", "true"]

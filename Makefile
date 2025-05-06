GCP_PROJECT_ID="learned-stone-454021-c8"
GCP_SA="dev-service-account@learned-stone-454021-c8.iam.gserviceaccount.com"
GCP_REGION="northamerica-south1"
ARTIFACT_REGISTRY_NAME="ai-agents"
AGENT_IMAGE_NAME="$(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/$(ARTIFACT_REGISTRY_NAME)/image-generator-agent:latest"
AGENT_API_IMAGE_NAME="$(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/$(ARTIFACT_REGISTRY_NAME)/ai_agent_api:latest"


gcloud-auth:
	gcloud config unset auth/impersonate_service_account 
	gcloud auth application-default login --impersonate-service-account $(GCP_SA)
	
uv-sync:
	uv sync --all-groups

install-git-hooks: 
	uv run pre-commit install
	uv run pre-commit install-hooks

run-agent:
	cd assistant_agent && \
	uv run python agent.py

run-agent-api:
	cd app/backend &&\
	uv run -- uvicorn main:app --reload

build-agent-api:
	cp pyproject.toml uv.lock app/backend/.
	docker build \
	-f app/backend/agent_api.dockerfile \
	-t $(AGENT_API_IMAGE_NAME) \
	.
	rm app/backend/pyproject.toml app/backend/uv.lock
	
push-agent-api:
	docker push $(AGENT_API_IMAGE_NAME)

run-app:
	cd app/frontend &&\
	uv run streamlit run agent_app.py

build-agent-app-image:
	docker build -f agent_app.dockerfile \
	-t $(AGENT_IMAGE_NAME) .

push-agent-image:
	docker push $(AGENT_IMAGE_NAME)

run-agent-app-container:
	docker run -p 8501:8501 $(AGENT_IMAGE_NAME)

run-tests:
	cd tests &&\
	uv run pytest
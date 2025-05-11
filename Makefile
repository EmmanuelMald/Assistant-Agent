GCP_PROJECT_ID="learned-stone-454021-c8"
GCP_SA="dev-service-account@learned-stone-454021-c8.iam.gserviceaccount.com"
GCP_REGION="northamerica-south1"
ARTIFACT_REGISTRY_NAME="ai-agents"
AGENT_UI_IMAGE_NAME="$(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/$(ARTIFACT_REGISTRY_NAME)/ai_agent_ui:test"
AGENT_API_IMAGE_NAME="$(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/$(ARTIFACT_REGISTRY_NAME)/ai_agent_api:test"


gcloud-auth:
	gcloud config unset auth/impersonate_service_account 
	gcloud auth application-default login --impersonate-service-account $(GCP_SA)
	
uv-sync:
	uv sync --all-groups

install-git-hooks: 
	uv run pre-commit install
	uv run pre-commit install-hooks

run-agent:
	uv run python -m assistant_agent.agent

run-agent-api:
	uv run -- uvicorn app.backend.main:app --reload

build-agent-api:
	cp pyproject.toml uv.lock app/backend/.
	docker build \
	-f app/backend/agent_api.dockerfile \
	-t $(AGENT_API_IMAGE_NAME) \
	.
	rm app/backend/pyproject.toml app/backend/uv.lock
	
push-agent-api:
	docker push $(AGENT_API_IMAGE_NAME)

run-agent-ui:
	cd app/frontend &&\
	uv run streamlit run agent_ui.py

build-agent-ui:
	cp pyproject.toml uv.lock app/frontend/.
	docker build \
	-f app/frontend/agent_ui.dockerfile \
	-t $(AGENT_UI_IMAGE_NAME) .
	rm app/frontend/pyproject.toml app/frontend/uv.lock

push-agent-image:
	docker push $(AGENT_UI_IMAGE_NAME)

run-agent-ui-image:
	docker run -p 8501:8501 $(AGENT_UI_IMAGE_NAME)

run-tests:
	uv run pytest
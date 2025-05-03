GCP_PROJECT_ID="learned-stone-454021-c8"
GCP_SA="dev-service-account@learned-stone-454021-c8.iam.gserviceaccount.com"
GCP_REGION="northamerica-south1"
EMBEDDING_SERVICE_IMAGE_NAME="northamerica-south1-docker.pkg.dev/$(GCP_PROJECT_ID)/dev-rag-llm-artifact/embedding_service:latest"


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
	uv run python hello_agent.py

run-app:
	cd app &&\
	uv run streamlit run app.py
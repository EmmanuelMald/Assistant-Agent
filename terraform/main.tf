provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
}

############### ARTIFACT REGISTRY ###############

resource "google_artifact_registry_repository" "ai_agents_artifact_registry" {
  location               = var.gcp_region
  repository_id          = var.artifact_registry_name
  format                 = "docker"
  cleanup_policy_dry_run = var.artifact_registry_dry_run
  cleanup_policies {
    id     = "delete_untagged_images"
    action = "DELETE"
    condition {
      tag_state  = "UNTAGGED"
      older_than = "10d" # after 10 days untagged, delete the image 
    }
  }
}


############### CLOUD RUN - AGENT API ###############

resource "google_cloud_run_v2_service" "agent_api_instance" {
  name                = var.agent_api_instance_name
  location            = var.gcp_region
  client              = "terraform"
  deletion_protection = false

  template {
    # Service account that the container will use to authenticate with GCP
    service_account = var.gcp_dev_sa

    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${var.artifact_registry_name}/${var.agent_api_image_name}:${var.agent_api_tag_image}"
      ports {
        container_port = var.agent_api_port
      }
      resources {
        limits = {
          memory = "2Gi"
          cpu    = "1"
        }
      }
    }
    scaling {
      # Min instances
      min_instance_count = 0
      max_instance_count = 2
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "agent_api_instance_auth" {
  location = google_cloud_run_v2_service.cloudrun_agent_api_instance.location
  name     = google_cloud_run_v2_service.cloudrun_agent_api_instance.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
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
  # Check documentation for vulnerability scanning
  # https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/artifact_registry_repository.html#nested_vulnerability_scanning_config
  vulnerability_scanning_config {
    enablement_config = "DISABLED"
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

# The service account in the CD that executes this, needs the run.services.setIamPolicy (in CloudRun Admin)
resource "google_cloud_run_v2_service_iam_member" "agent_api_instance_auth" {
  location = google_cloud_run_v2_service.agent_api_instance.location
  name     = google_cloud_run_v2_service.agent_api_instance.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

#################### CLOUD RUN - AGENT UI #######################

resource "google_cloud_run_v2_service" "agent_ui_instance" {
  name                = var.agent_ui_instance_name
  location            = var.gcp_region
  client              = "terraform"
  deletion_protection = false

  template {
    # Service account that the container will use to authenticate with GCP
    service_account = var.gcp_dev_sa

    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${var.artifact_registry_name}/${var.agent_ui_image_name}:${var.agent_ui_tag_image}"
      ports {
        container_port = var.agent_ui_port
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

# The service account in the CD that executes this, needs the run.services.setIamPolicy (in CloudRun Admin)
resource "google_cloud_run_v2_service_iam_member" "agent_ui_instance_auth" {
  location = google_cloud_run_v2_service.agent_ui_instance.location
  name     = google_cloud_run_v2_service.agent_ui_instance.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

############### BIGQUERY ###############
resource "google_bigquery_dataset" "ai_agent_dataset" {
  dataset_id  = var.dataset_id
  description = "The datasets in Bigquery can be considered as schemas in any other structured database. So this is the schema for the tables."
  location    = var.gcp_region

  labels = {
    env = "default"
  }
}

resource "google_bigquery_table" "ai_agent_users_table" {
  dataset_id = google_bigquery_dataset.ai_agent_dataset.dataset_id
  table_id   = var.users_table_id

  labels = {
    env         = "default"
    primary_key = "user_id"
  }

  schema = <<EOF

[
  {
    "name": "user_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "User identifier"
  },
  {
    "name": "company_name",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Company where the user works"
  },
  {
    "name": "created_at",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "Timestamp when the user was created"
  },
  {
   "name": "full_name",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Full name of the user"
  },
  {
    "name": "email",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Email of the user"
  },
  {
    "name": "company_role",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Role of the user in the company"
  },
  {
    "name": "hashed_password",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Hashed password"
  }
]
EOF
}



resource "google_bigquery_table" "ai_agent_chat_sessions_table" {
  dataset_id = google_bigquery_dataset.ai_agent_dataset.dataset_id
  table_id   = var.chat_sessions_table_id

  labels = {
    env = "default"
  }

  schema = <<EOF

[
  {
    "name": "chat_session_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Id of the chat session"
  },
  {
    "name": "user_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Id of the user who started the chat session"
  },
  {
    "name": "created_at",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "Timestamp when the chat session was created"
  }
]
EOF
}


resource "google_bigquery_table" "ai_agent_prompts_table" {
  dataset_id = google_bigquery_dataset.ai_agent_dataset.dataset_id
  table_id   = var.prompts_table_id

  labels = {
    env = "default"
  }

  schema = <<EOF

[
  {
    "name": "prompt_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Id of the prompt"
  },
  {
    "name": "chat_session_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Id of the chat session"
  },
  {
    "name": "created_at",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "Timestamp when the prompt was created"
  },
  {
    "name": "prompt",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "User prompt"
  },
  {
    "name": "response",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "AI Agent prompt"
  }
]
EOF
}

resource "google_bigquery_table" "ai_agent_steps_table" {
  dataset_id = google_bigquery_dataset.ai_agent_dataset.dataset_id
  table_id   = var.agent_steps_table_id

  labels = {
    env = "default"
  }

  schema = <<EOF

[
  {
    "name": "chat_session_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Id of the chat session"
  },
  {
    "name": "prompt_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Id of the prompt"
  },
  {
    "name": "step_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Id of agent step"
  },
  {
    "name": "created_at",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "Time when the step was created"
  },
  {
    "name": "step_data",
    "type": "JSON",
    "mode": "REQUIRED",
    "description": "Step data"
  }
]
EOF
}

# To check data types: https://developer.hashicorp.com/terraform/language/expressions/types

variable "gcp_project_id" {
  type        = string
  description = "GCP project id"
  default     = "learned-stone-454021-c8"
}

variable "gcp_region" {
  type        = string
  description = "GCP region where the resources will be stored"
  default     = "northamerica-south1"
}

variable "gcp_zone" {
  type        = string
  description = "GCP zone within the gcp_region"
  default     = "northamerica-south1-a"
}

variable "gcp_dev_sa" {
  type        = string
  description = "GCP Service Account that CloudRun will use to authenticate"
  default     = "dev-service-account@learned-stone-454021-c8.iam.gserviceaccount.com"
}

variable "artifact_registry_name" {
  type        = string
  description = "Name of the artifact registry to create"
  default     = "ai-agents"
}

variable "artifact_registry_dry_run" {
  type        = bool
  description = "Determines if cleanup policies delete artifacts. true: No artifacts are deleted. false: Artifacts are deleted or kept depending on the policies"
  default     = false
}

variable "agent_api_instance_name" {
  type        = string
  description = "Name of the CloudRun instance that contains the agent API"
  default     = "agent-api"
}

variable "agent_api_image_name" {
  type        = string
  description = "Name of the agent api docker image"
  default     = "agent_api"
}

variable "agent_api_tag_image" {
  type        = string
  description = "Tag of the docker image"
  default     = "latest"
}

variable "agent_api_port" {
  type        = number
  description = "Port where the container of the agent API will listen"
  default     = 8000
}

variable "agent_ui_instance_name" {
  type        = string
  description = "Name of the CloudRun instance that contains the agent UI"
  default     = "agent-app"
}

variable "agent_ui_image_name" {
  type        = string
  description = "Name of the docker image of the the agent UI"
  default     = "agent_app"
}

variable "agent_ui_tag_image" {
  type        = string
  description = "Tag of the docker image of the the agent UI"
  default     = "latest"
}

variable "agent_ui_port" {
  type        = number
  description = "Port where the container will listen"
  default     = 8501
}

# Due to terraform will be executed in a CI/CD, and each step is 
# executed in a container. Every time the terraform apply is executed, the tf.state
# is lost when the container is turned off. So the tf.state needs to exists in gcs
terraform {
  backend "gcs" {
    bucket = "rag_llm_energy_expert"
    prefix = "terraform/state"
  }
}
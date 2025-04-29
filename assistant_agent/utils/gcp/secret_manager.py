from google.cloud import secretmanager
from typing import Union
from pydantic import SecretStr
from loguru import logger

# Create a SecretManager Client
client = secretmanager.SecretManagerServiceClient()


def secret_exists(secret_id: str, project_id: str) -> None:
    """
    Checks if a secret already exists

    Args:
        project_id: str -> GCP project_id
        secret_id: str -> Name of the secret to find

    Return:
        bool -> True if the secret exists
    """
    if not isinstance(secret_id, str) or not isinstance(project_id, str):
        raise TypeError("The parameters secret_id and project_id must be strings")

    if secret_id == "" or project_id == "":
        raise ValueError("Neither secret_id nor project_id can be empty strings")

    parent = f"projects/{project_id}"

    # Get secret objects and names
    secret_objects = client.list_secrets(request={"parent": parent})

    # secret.name is in the form: "projects/project_id/secrets/secret_id"
    secret_names = [secret.name.split("/")[-1] for secret in secret_objects]

    if secret_id in secret_names:
        return True

    return False


def secret_version_exists(
    secret_id: str,
    version_id: Union[str, int],
    project_id: str,
):
    """
    Return True if a version of a secret exists

    Args:
        secret_id: str -> Name of the secret to get
        version_id: Union[str, int] -> Version of the secret
        project_id: str -> GCP project id
    """
    # secret_exists has error handlers
    if not secret_exists(secret_id, project_id):
        raise ValueError("The secret_id does not exists")

    if not isinstance(version_id, Union[str, int]) or version_id == "":
        raise TypeError("version_id is not a string or an integer")

    parent = client.secret_path(project_id, secret_id)

    versions = client.list_secret_versions(request={"parent": parent})

    # version.name is in the form:
    # "projects/project_id/secrets/secret_id/versions/version_id"
    version_names = [version.name.split("/")[-1] for version in versions]

    # Convert version_id into a string to compare it with version_names
    version_id = str(version_id)

    if version_id in version_names:
        return True

    return False


def create_secret(
    secret_id: str,
    secret_value: str,
    project_id: str,
) -> None:
    """
    Creates a secret on SecretManager.
    Code obtained from:
    https://cloud.google.com/secret-manager/docs/create-secret-quickstart

    Args:
        secret_id: str -> Name of the secret
        secret_value: str -> Value to store in secret manager
        project_id: str -> GCP project_id

    Return:
        None
    """
    parameters = [secret_id, secret_value, project_id]
    if not all([isinstance(x, str) for x in parameters]):
        raise TypeError(f"The parameters {','.join(parameters)} must be strings")

    if secret_exists(secret_id, project_id):
        raise ValueError(
            "The secret already exists. Try creating a new "
            "version of this secret or write a new secret_id"
        )

    # Create the parent secret
    secret = client.create_secret(
        request={
            "parent": f"projects/{project_id}",
            "secret_id": secret_id,
            "secret": {"replication": {"automatic": {}}},
        }
    )

    # Add the secret version
    client.add_secret_version(
        request={"parent": secret.name, "payload": {"data": secret_value}}
    )

    logger.info("Secret created")


def get_secret(
    secret_id: str,
    version_id: Union[int, str],
    project_id: str,
) -> str:
    """
    Get a secret from secretmanager
    Code obtained from:
    https://cloud.google.com/secret-manager/docs/access-secret-version

    Args:
        secret_id: str -> Name of the secret
        version_id: Union[int, str] -> Version of the secret

    Return:
        SecretStr -> string with the version of the secret
    """
    # secret_version_exists contains error handlers for all the parameters
    if not secret_version_exists(secret_id, version_id, project_id):
        raise ValueError("The version_id does not exists")

    # Build the resource name
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version
    response = client.access_secret_version(request={"name": name})

    # Get the payload of the response
    payload = SecretStr(response.payload.data.decode("UTF-8"))

    return payload


def destroy_secret_version(
    secret_id: str,
    version_id: str,
    project_id: str,
):
    """
    Destroy a secret version.

    Args:
        project_id: str -> GCP project_id
        secret_id: str -> Name of the secret to destroy
        version_id: str -> Version of the secret to destroy

    Return:
        None
    """
    # secret_version_exists contains error handlers for all the parameters
    if not secret_version_exists(secret_id, version_id, project_id):
        raise ValueError("The secret version does not exists")

    # create the whole path to the secret
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Destroy the secret version
    response = client.destroy_secret_version(request={"name": name})

    logger.info(f"Secret version destroyed: {response.name}")


def delete_secret(
    secret_id: str,
    project_id: str,
):
    """
    Deleting a secret is an irreversible operation.
    Deletes a secret and all its versions.

    Args:
        secret_id: str -> Name of the secret to delete
        project_id: str -> GCP project_id

    Return:
        None
    """
    # secret_exists has error handlers
    if not secret_exists(secret_id, project_id):
        raise ValueError("The secret_id does not exists")

    name = client.secret_path(project_id, secret_id)

    client.delete_secret(request={"name": name})

    logger.info("Secret deleted")


def add_secret_version(
    secret_id: str,
    secret_value: str,
    project_id: str,
) -> None:
    """
    Add a new version to a secret_id. Adding a new version means set a new
    value to the secret.

    Args:
        secret_id: str -> secret_id to add a version
        secret_value: str -> New value for the secret_id
        project_id: str -> GCP project id

    Return:
        None
    """
    # secret_exists already contains error handlers
    if not secret_exists(secret_id, project_id):
        raise ValueError(
            "The secret_id does not exists, use the function 'create_secret' instead"
        )

    parent = client.secret_path(project_id, secret_id)

    # Encode the secret using UTF-8
    secret_value_bytes = secret_value.encode("UTF-8")

    # Add the secret version
    client.add_secret_version(
        request={
            "parent": parent,
            "payload": {"data": secret_value_bytes},
        }
    )

    logger.info("Secret version added")

from google.cloud import storage
from loguru import logger
import os
from io import BytesIO


# Create a general storage client
client = storage.Client()


def bucket_exists(bucket_name: str) -> bool:
    """
    Tells if a bucket exists or not.

        Args:
            bucket_name: str -> Name of the bucket

        Return:
            bool -> True if the bucket exists, otherwise False.
    """
    if not isinstance(bucket_name, str) or bucket_name == "":
        raise TypeError("The parameter bucket_name must be a not null string")

    return client.bucket(bucket_name).exists()


def blob_exists(blob_name: str, bucket_name: str) -> bool:
    """
    Checks if the blob in the bucket exists.

    Args:
        blob_name: Name of the file to verify if exists.
                            Ex: "gcs_folder1/file.txt"

        bucket_name: Name of the bucket. Ex: "my_bucket"

    Returns: bool
    """
    # bucket_exists already has error handlers
    if bucket_exists(bucket_name):
        # Error handlers for the blob_name
        if not isinstance(blob_name, str) or blob_name == "":
            raise TypeError(
                "The parameter blob_name must not be empty and must be of type string"
            )

    else:
        raise ValueError(f"The bucket {bucket_name} does not exists")

    # Get a list of objects inside the bucket
    blobs = client.list_blobs(bucket_name)

    blobs_name = [blob.name for blob in blobs]

    if blob_name in blobs_name:
        return True

    return False


def create_bucket(bucket_name: str, location: str) -> storage.Client.bucket:
    """
    Create a new bucket on GCP

    Args:
        bucket_name: str -> Name of the bucket

    Return:
        None
    """
    if bucket_exists(bucket_name):
        raise ValueError(f"The bucket {bucket_name} already exists")

    bucket = client.create_bucket(bucket_name, location=location)
    logger.info(f"Bucket {bucket_name} successfully created!")

    return bucket


def delete_bucket(bucket_name: str) -> None:
    """
    Delete a bucket.

    Args:
        bucket_name: str -> Name of the bucket to remove

    Return:
        None
    """
    if not bucket_exists(bucket_name):
        raise ValueError(f"The bucket {bucket_name} does not exists")

    bucket = client.get_bucket(bucket_name)
    bucket.delete()

    logger.info(f"Bucket {bucket_name} deleted")

    return


def upload_file(
    origin_file_path: str,
    bucket_name: str,
    destination_file_path: str = None,
):
    """
    Upload a local file into a GCS bucket.

        Args:
            bucket_name: str -> Name of the bucket. Ex: "my_first_bucket"
            origin_file_path: str -> Local path of the file to be uploaded
                                Ex: C:Users/my_folder/file.txt
            destination_file_path: str -> GCS path of the file to be uploaded
                                Ex: gcs_folder/new_file.txt
    """
    # Checks for the origin_file_path parameter
    if not isinstance(origin_file_path, str) or origin_file_path == "":
        raise ValueError(
            "The parameter origin_file_path cannot be empty, and must be a string"
        )

    if not os.path.isfile(origin_file_path):
        raise ValueError(
            f"The file {origin_file_path} does not exists, check the path and try again."
        )

    origin_file_path = origin_file_path.replace("\\", "/")

    # Checks for the destination_file_path parameter
    if destination_file_path is None:
        destination_file_path = origin_file_path.split("/")[-1]

    elif not isinstance(destination_file_path, str):
        raise ValueError(
            "The parameter destination_file_path must be a string. If not passed, the file "
            "will be stored in the root of the bucket with the exact name as the original file"
        )

    # Check for the bucket_name parameter, the bucket_exists function has error handlers
    if not bucket_exists(bucket_name):
        raise ValueError(f"The bucket {bucket_name} does not exists")

    # Get the bucket
    bucket = client.bucket(bucket_name)

    # Upload file in the bucket
    blob = bucket.blob(destination_file_path)
    blob.upload_from_filename(origin_file_path)

    logger.info(
        f"{origin_file_path.split('/')[-1]} stored in GCS as {destination_file_path}"
    )


def upload_image_from_memory(
    blob_name: str,
    image: BytesIO,
    bucket_name: str,
) -> None:
    """
    Upload an image to a GCS bucket

    Args:
        blob_name: str -> Path + name of the file to be stored. ex: "my_folder/my_image.png"
        image: BytesIO -> Image to be stored in GCS.
        bucket_name: str -> Name of the GCS bucket. ex: "my_bucket"

    Return:
        None
    """
    if not bucket_exists(bucket_name):
        raise ValueError(f"The bucket {bucket_name} does not exists")
    if not isinstance(image, BytesIO):
        raise TypeError("The image parameter must be a BytesIO object")

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_file(image)

    blob.make_public()

    logger.info("Image successfully stored in GCS bucket")

    return blob.public_url


def upload_file_from_memory(
    blob_name: str,
    string_data: str,
    bucket_name: str,
) -> None:
    """
    Uploading from memory is useful for when you want to avoid unnecessary writes from memory
    to your local file system.

    Args:
        blob_name: str -> Path + name of the file to be stored. ex: "my_folder/my_file.txt"
        string_data: str -> Data to be stored in GCS. Must be converted to string
        bucket_name: str -> Name of the GCS bucket. ex: "my_bucket"

    Return:
        None
    """
    if not bucket_exists(bucket_name):
        raise ValueError(f"The bucket {bucket_name} does not exists")
    if not isinstance(string_data, str) or not isinstance(blob_name, str):
        raise ValueError(
            "The parameters string_data and blob_name must be string types"
        )

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(string_data)

    logger.info("In-memory data successfully stored in GCS bucket")


def delete_file(file_name: str, bucket_name: str) -> None:
    """
    Delete a file from a bucket

    Args:
        bucket_name: str -> Name of the bucket.
        file_name: str -> Path of the GCS file: Ex. gcs_folder/file.txt

    Return:
        None
    """
    if not blob_exists(blob_name=file_name, bucket_name=bucket_name):
        raise ValueError(
            f"The file {file_name} does not exist in the bucket {bucket_name}"
        )

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.delete()
    logger.info(f"The file {file_name} was deleted successfully")


def download_file(gcs_file_path: str, local_file_path: str, bucket_name: str) -> None:
    """
    Download a file stored in a bucket of GCS into a local path.

    Args:
        gcs_file_path: str -> Path to the file to download. Ex: "gcs_folder/my_file.pdf"
        local_file_path: str -> Local path where the file will be stored. Ex. "local_folder/my_file.pdf"
        bucket_name: str -> Name of the bucket where the file is stored. Ex. "my_bucket"

    Return:
        None.
    """
    if not blob_exists(gcs_file_path, bucket_name):
        raise ValueError(f"The file: {gcs_file_path} does not exists")

    if not isinstance(local_file_path, str):
        raise ValueError("local_file_path must be a string")

    file_path = "/".join(local_file_path.split("/")[:-1])

    if not os.path.isdir(file_path):
        raise ValueError(f"The path {file_path} does not exists")

    # Get the bucket and the file
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_file_path)

    # Download the file
    blob.download_to_filename(local_file_path)
    logger.info(f"file {gcs_file_path} downloaded in {local_file_path}")


def get_file(
    gcs_file_path: str,
    bucket_name: str,
) -> bytes:
    """
    Download a file stored in GCS directly in memory to be processed.

    Args:
        gcs_file_path: str -> Path to the file. ex: "my_folder/file.txt"
        bucket_name: str -> The GCS bucket where the file is stored. ex: "my_bucket"

    Return:
        bytes -> Bytes of the file
    """
    # blob_exists already has error handlers
    if not blob_exists(gcs_file_path, bucket_name):
        raise ValueError(
            f"{gcs_file_path} does not exists. Check the path and try again"
        )

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_file_path)

    memory_blob = blob.download_as_bytes()

    return memory_blob

from loguru import logger
from pydantic import SecretStr

import sys

sys.path.append("../..")

from app.backend.models import UserInDB
from assistant_agent.utils.gcp.bigquery import query_data
from assistant_agent.config import GCPConfig


gcp_config = GCPConfig()

project_id = gcp_config.PROJECT_ID
dataset_id = gcp_config.BQ_DATASET_ID


def user_in_db(email: str, table_id: str = gcp_config.USERS_TABLE_NAME) -> UserInDB:
    """
    Defines if a user already exists in the database.

    Args:
        email: str -> The email of the user.
        table_id: str -> Name of the table that contains the user's email

    Returns:
        UserInDB -> UserInDB class containing the hashed_password
    """
    logger.info("Verifying if the user is already registered...")

    table_id = gcp_config.USERS_TABLE_NAME

    query = f"""
            select
                hashed_password
            from {project_id}.{dataset_id}.{table_id}
            where email = '{email}'
            """
    logger.debug(f"{query=}")

    rows_iterator = query_data(query)

    user_id = [SecretStr(row.hashed_password) for row in rows_iterator]

    if len(user_id) > 0:
        return UserInDB(hashed_password=user_id[0])

    return UserInDB(hashed_password=None)


def generate_user_id(table_id: str = gcp_config.USERS_TABLE_NAME) -> str:
    """
    Generates a new user id based on the current users registered in the DB

    Args:
        table_id: str -> Name of the table that contains the user's email

    Returns:
    """
    query_count_users = f"""
            select
                count(*) as total_users
            from {project_id}.{dataset_id}.{table_id}
    """

    # Query the BigQuery database to get the total number of users
    rows = query_data(query=query_count_users)
    total_users = [row.total_users for row in rows][0]

    # Generating the user ID
    next_id = total_users + 1
    user_id = f"UID{next_id:05d}"

    return user_id

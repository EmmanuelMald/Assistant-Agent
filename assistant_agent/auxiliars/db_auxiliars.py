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

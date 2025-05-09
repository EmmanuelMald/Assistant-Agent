from loguru import logger
from datetime import datetime
from pydantic import SecretStr

import sys

sys.path.append("../..")

from assistant_agent.schemas import UserInDB, User
from assistant_agent.utils.gcp.bigquery import query_data, insert_rows
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


def insert_user_data(user_data: User, table_id=gcp_config.USERS_TABLE_NAME) -> str:
    """
    Insert user data into the BigQuery database.

    Args:
        user_data: User -> User class containing the user information
        table_id (str): The name of the BigQuery table.

    Returns:
        str -> user_id that was inserted into the BigQuery table.
    """
    logger.info("Inserting user data into BigQuery...")

    # Get the current date and time
    now = datetime.now()
    current_time = now.strftime(r"%Y-%m-%d %H:%M:%S")

    logger.info("Generating a new user ID...")
    user_id = generate_user_id(table_id=table_id)
    logger.info(f"Generated user ID: {user_id}")

    logger.info("Inserting data...")
    # Preparing the columns to fill in the BigQuery table
    data_to_insert = {
        "user_id": user_id,
        "full_name": user_data.full_name,
        "company_name": user_data.company_name,
        "email": user_data.email,
        "company_role": user_data.company_role,
        "created_at": current_time,
        "last_entered_at": current_time,
        "hashed_password": user_data.password.get_secret_value(),  # Supposing that password is already hashed
    }

    # Insert the data into the BigQuery table
    insert_rows(
        project_id=project_id,
        dataset_name=dataset_id,
        table_name=table_id,
        rows=[
            data_to_insert,
        ],
    )
    logger.info("user data successfully added to the database")
    return user_id

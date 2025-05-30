from pydantic import SecretStr, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone
import jwt
from assistant_agent.utils.auth_auxiliars import verify_password
from assistant_agent.schemas import User
from assistant_agent.credentials import get_auth_config
from assistant_agent.database.tables.bigquery import BQUsersTable
from loguru import logger


auth_config = get_auth_config()

users_table = BQUsersTable()


def authenticate_user(email: EmailStr, password: SecretStr) -> Optional[User]:
    """
    Decides if the user needs to be authenticated based on the existance of its database identifier, in this case,
    the email, and its password

    Args:
        email: str -> User's email
        password: SecretStr -> User's password

    Returns:
        Optional[User] -> Returns the user's data in the DB in case the email and password matches
    """
    user_id = users_table.email_in_table(email)
    if not user_id:
        return None
    user_data = users_table.get_user_data(user_id)
    if not verify_password(password, user_data.password):
        return None
    return user_data


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates an access token for the user

    Args:
        data: dict -> Must include the data that you want to be included inside the token
                      By convention, one parameter should be {'sub': subject_id }
        expires_delta: Optional[timedelta] -> token lifetime limit

    """
    to_encode = data.copy()
    logger.info("Creating access token...")

    # Set the expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # exp = expiration time in JWT
    to_encode.update({"exp": expire})
    logger.info(f"Token expires at {expire}")

    encoded_jwt = jwt.encode(
        to_encode,
        auth_config.SECRET_KEY.get_secret_value(),
        algorithm=auth_config.ALGORITHM,
    )
    logger.info("Access token successfully created")

    return encoded_jwt

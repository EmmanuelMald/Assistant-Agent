from pydantic import SecretStr, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone
import jwt
from assistant_agent.auxiliars.auth_auxiliars import verify_password
from assistant_agent.schemas import UserInDB
from assistant_agent.credentials import get_auth_config
from assistant_agent.database.tables.bigquery import BQUsersTable


auth_config = get_auth_config()

users_table = BQUsersTable()


def authenticate_user(email: EmailStr, password: SecretStr) -> Optional[UserInDB]:
    """
    Decides if the user needs to be authenticated based on the existance of its database identifier, in this case,
    the email, and its password

    Args:
        email: str -> User's email
        password: SecretStr -> User's password

    Returns:
        Optional[UserInDB] -> Returns the user's data in the DB in case the email and password matches
    """
    user_id = users_table.email_in_table(email)
    if not user_id:
        return None
    user_data = users_table.get_user_data(user_id)
    if not verify_password(password, user_data.password):
        return None
    return user_data


def create_acess_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates an access token for the user

    Args:
        data: dict -> Must be in the format {"sub": user_identifier}
        expires_delta: Optional[timedelta] -> token lifetime limit

    """
    to_encode = data.copy()

    # Set the expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, auth_config.SECRET_KEY, algorithm=auth_config.ALGORITHM
    )

    return encoded_jwt

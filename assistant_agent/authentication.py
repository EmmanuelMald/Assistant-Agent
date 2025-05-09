from pydantic import SecretStr
from typing import Union, Optional
from datetime import datetime, timedelta, timezone
import jwt
import sys

sys.path.append("../..")

from assistant_agent.auxiliars.auth_auxiliars import verify_password
from assistant_agent.schemas import UserInDB
from assistant_agent.auxiliars.db_auxiliars import user_in_db
from assistant_agent.credentials import get_auth_config


auth_config = get_auth_config()


def authenticate_user(email: str, password: SecretStr) -> Union[UserInDB, bool]:
    """
    Decides if the user needs to be authenticated based on the existance of its database identifier, in this case,
    the email, and its password

    Args:
        email: str -> User's email
        password: SecretStr -> User's password

    Returns:
        Union[UserInDB, bool] -> Return false if the user should not be authenticated, and the UserInDB class in case
                                 the email and password matches
    """
    user_data = user_in_db(email=email)
    if not user_data.hashed_password:
        return False
    if not verify_password(
        plain_password=password, hashed_password=user_data.hashed_password
    ):
        return False
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

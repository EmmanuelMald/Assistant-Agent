from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
import jwt
from loguru import logger
from assistant_agent.credentials import get_auth_config
from assistant_agent.config import APIConfig
from app.backend.models import TokenData

auth_config = get_auth_config()
api_config = APIConfig()

token_url = api_config.LOGIN_ENDPOINT.replace("/", "")
# tokenUrl must point to the endpoint where the token will be generated
# Extracts the "Bearer" token from the "Authorization" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=token_url)


async def get_current_user_id_from_token(token: str = Depends(oauth2_scheme)) -> str:
    """
    FastAPI dependence to:
        - Extract the token from the authorization header: Bearer <token>
        - Decode and validate the JWT
        - Extract the user_id from the token

    Depends is executed first to get the token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    expired_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            auth_config.SECRET_KEY.get_secret_value(),
            algorithms=[
                auth_config.ALGORITHM,
            ],
        )

        user_id_from_token = payload["sub"]

        if not user_id_from_token:
            logger.warning("Valid token without 'sub' claim")
            raise credentials_exception

        # Verifying that the user_id is aligned with the expected format
        token_data = TokenData(user_id=user_id_from_token)

    except jwt.ExpiredSignatureError:
        logger.warning("Attempt access with expired token")
        raise expired_token_exception

    except jwt.PyJWTError as e:
        logger.warning(f"JWT Validation Error: {e}")
        raise credentials_exception

    except ValidationError as e:
        logger.warning(f"Invalid token payload: {e}")

    except Exception:
        logger.error("Unexpected error during token decoding...")
        raise credentials_exception

    return token_data.user_id

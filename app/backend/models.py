from pydantic import BaseModel, Field
from typing import Annotated
from assistant_agent.schemas import (
    USER_ID_FIELD,
    EMAIL_FIELD,
    PASSWORD_FIELD,
    CHAT_SESSION_ID_FIELD,
    STRING_NORMALIZER,
)


class AgentRequest(BaseModel):
    current_user_prompt: Annotated[
        str,
        Field(description="User prompt", min_length=1),
        STRING_NORMALIZER,
    ]
    chat_session_id: CHAT_SESSION_ID_FIELD


class AgentResponse(BaseModel):
    agent_response: Annotated[
        str, Field(description="Agent response"), STRING_NORMALIZER
    ]
    chat_session_id: CHAT_SESSION_ID_FIELD


class TokenResponse(BaseModel):
    access_token: Annotated[
        str,
        Field(description="Token generated"),
    ]
    token_type: Annotated[
        str,
        Field(default="bearer", description="type of token generated"),
    ]
    username: Annotated[str, Field(description="Name of the user")]


class TokenData(BaseModel):
    # Defines the expected structure of the data inside the token
    user_id: USER_ID_FIELD


class UserLoginRequest(BaseModel):
    email: EMAIL_FIELD
    password: PASSWORD_FIELD

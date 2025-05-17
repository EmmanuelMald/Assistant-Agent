from pydantic import BaseModel, Field, EmailStr, SecretStr
from assistant_agent.schemas import (
    USER_ID_FIELD,
    PASSWORD_FIELD,
    CHAT_SESSION_ID_FIELD,
)


class AgentRequest(BaseModel):
    current_user_prompt: str = Field(description="User prompt", min_length=1)
    chat_session_id: CHAT_SESSION_ID_FIELD


class AgentResponse(BaseModel):
    agent_response: str = Field(description="Agent response")
    chat_session_id: CHAT_SESSION_ID_FIELD


class TokenResponse(BaseModel):
    access_token: str = Field(description="Token generated")
    token_type: str = Field(default="bearer", description="type of token generated")
    username: str = Field(description="Name of the user")


class TokenData(BaseModel):
    # Defines the expected structure of the data inside the token
    user_id: USER_ID_FIELD


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(description="User's email")
    password: SecretStr = PASSWORD_FIELD

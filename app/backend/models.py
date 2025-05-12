from pydantic import BaseModel, Field
from typing import Optional
from assistant_agent.schemas import USER_ID_FIELD


class AgentRequest(BaseModel):
    chat_history: Optional[str] = Field(
        default="[]",
        description="History of the current chat",
    )
    current_user_prompt: str = Field(description="User prompt", min_length=1)


class AgentResponse(BaseModel):
    agent_response: str = Field(description="Agent response")
    current_history: str = Field(description="Whole chat session history")


class UserRegistrationResponse(BaseModel):
    user_id: str = USER_ID_FIELD
    message: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Defines the expected structure of the data inside the token"""

    user_id: str = USER_ID_FIELD

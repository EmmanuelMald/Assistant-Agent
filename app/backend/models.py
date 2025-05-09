from pydantic import BaseModel, Field
from typing import Optional
import sys

sys.path.append("../..")


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
    user_id: str
    message: str

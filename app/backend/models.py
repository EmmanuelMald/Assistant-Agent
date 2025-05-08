from pydantic import BaseModel, Field, EmailStr
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


class User(BaseModel):
    full_name: str = Field(description="Full name of the user")
    company_name: Optional[str] = Field(
        default=None, description="Name of the company where the user works for"
    )
    email: EmailStr = Field(description="User's email")
    company_role: Optional[str] = Field(
        default=None,
        description="Role that the user has in the company where he's working on",
    )

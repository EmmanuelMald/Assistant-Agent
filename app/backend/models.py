from pydantic import BaseModel, Field, EmailStr, field_validator, SecretStr
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
    """
    This class will receive the data obtained when the user logs by the first time or
    when trying to login
    """

    full_name: str = Field(
        default=None,  # Only in case this field is not passed
        description="Full name of the user",
        min_length=1,
        pattern=r"^[^\s].*",  # To not start with a space
    )
    company_name: Optional[str] = Field(
        default=None,  # Only in case this field is not passed
        description="Name of the company where the user works for",
        pattern=r"^[^\s].*",  # To not start with a space
    )
    email: EmailStr = Field(description="User's email")
    company_role: Optional[str] = Field(
        default=None,  # Only in case this field is not passed
        description="Role that the user has in the company where he's working on",
        pattern=r"^[^\s].*",  # To not start with a space
    )
    password: SecretStr = Field(
        description="User's password. Must be at least 8 characters long.",
        min_length=8,
    )

    @field_validator("full_name", mode="after")
    @classmethod
    def normalize_full_name(cls, value):
        return value.strip().title()

    @field_validator("company_name", mode="after")
    @classmethod
    def normalize_company_name(cls, value):
        if value not in [None, ""]:
            return value.strip().title()
        return None

    @field_validator("company_role", mode="after")
    @classmethod
    def normalize_company_role(cls, value):
        if value not in [None, ""]:
            return value.strip().title()
        return None


class UserInDB(BaseModel):
    hashed_password: Optional[SecretStr] = Field(
        description="Hashed password stored in DB"
    )

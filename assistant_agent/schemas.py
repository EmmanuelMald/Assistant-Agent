from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    field_validator,
    SecretStr,
)
from typing import Optional


class User(BaseModel, validate_assignment=True):
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


class ChatSession(BaseModel, validate_assignment=True):
    user_id: str = Field(
        description="Id of the owner of the session", pattern=r"^UID\d{5}$"
    )


class UserInDB(BaseModel):
    hashed_password: Optional[SecretStr] = Field(
        description="Hashed password stored in DB"
    )


class Prompt(BaseModel, validate_assignment=True):
    chat_session_id: str = Field(
        description="ID of the user's chat session", pattern=r"^CSID\d+-\d{3}$"
    )
    user_id: str = Field(
        description="Id of the owner of the session", pattern=r"^UID\d{5}$"
    )
    prompt: str = Field(description="User's prompt", pattern=r"^\w.*", min_length=1)
    response: str = Field(description="Agent response", pattern=r"^\w.*", min_length=1)


class AgentStep(BaseModel, validate_assignment=True):
    chat_session_id: str = Field(
        description="ID of the user's chat session", pattern=r"^CSID\d+-\d{3}$"
    )
    prompt_id: str = Field(description="ID of the prompt", pattern=r"^PID\d{6}")
    step_data: dict = Field(
        description="Dictionary with all the data related to the agent's step"
    )

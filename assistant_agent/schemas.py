from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    field_validator,
    SecretStr,
)
from datetime import datetime
from typing import Optional
import json


# Common fields
USER_ID_FIELD = Field(description="ID of the user", pattern=r"^UID\d{5}$")
CHAT_SESSION_ID_FIELD = Field(
    description="ID of the user's chat session", pattern=r"^CSID\d+-\d{3}$"
)
PROMPT_ID_FIELD = Field(description="ID of the prompt.", pattern=r"^PID\d{6}$")
PASSWORD_FIELD = Field(
    description="User's password. Must be at least 8 characters long.",
    min_length=8,
)
TIMESTAMP_FORMAT = r"%Y-%m-%d %H:%M:%S"


class User(BaseModel, validate_assignment=True):
    """
    This class will receive the data obtained when the user logs by the first time or
    when trying to login
    """

    full_name: str = Field(
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
    password: SecretStr = PASSWORD_FIELD

    @field_validator("full_name", mode="after")
    @classmethod
    def normalize_full_name(cls, value):
        return value.strip().title()

    @field_validator("company_name", mode="after")
    @classmethod
    def normalize_company_name(cls, value):
        if value not in [None, ""]:
            return value.strip().upper()
        return None

    @field_validator("company_role", mode="after")
    @classmethod
    def normalize_company_role(cls, value):
        if value not in [None, ""]:
            return value.strip().upper()
        return None


class UserInDB(User):
    user_id: str = USER_ID_FIELD
    created_at: datetime = Field(
        description=r"datetime.datetime object with the timestamp when the user was created in the DB",
    )


class ChatSession(BaseModel, validate_assignment=True):
    user_id: str = USER_ID_FIELD


class Prompt(BaseModel, validate_assignment=True):
    chat_session_id: str = CHAT_SESSION_ID_FIELD
    user_id: str = USER_ID_FIELD
    prompt: str = Field(description="User's prompt", pattern=r"^\w.*", min_length=1)
    response: str = Field(description="Agent response", pattern=r"^\w.*", min_length=1)


class AgentStep(BaseModel, validate_assignment=True):
    chat_session_id: str = CHAT_SESSION_ID_FIELD
    prompt_id: str = PROMPT_ID_FIELD
    step_data: dict = Field(
        description="Dictionary with all the data related to the agent's step"
    )

    @field_validator("step_data", mode="after")
    @classmethod
    def prepare_json(cls, value):
        return json.dumps(value)


class ChatSessionData(ChatSession):
    chat_session_id: str = (CHAT_SESSION_ID_FIELD,)
    created_at: datetime = Field(description="Datetime when the session was created")

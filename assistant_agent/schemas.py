from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    field_validator,
    SecretStr,
    model_validator,
)
from typing import Optional
from datetime import datetime


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
    chat_session_id: Optional[str] = Field(
        default=None, description="ID of the chat session", pattern=r"CSID\d+-\d{3}$"
    )
    created_at: Optional[str] = Field(
        default=None,
        description="Date where the chat session was created. In format YYYY-MM-DD",
        pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
    )
    last_used_at: Optional[str] = Field(
        default=None,
        description="Last date when the session was used. In format YYYY-MM-DD",
        pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
    )
    session_history: Optional[str] = Field(
        default="[]", description="Full chat session history"
    )

    @field_validator("session_history", mode="after")
    @classmethod
    def session_history_handle_nulls(cls, value):
        if value is None:
            return "[]"
        return value

    @model_validator(mode="after")
    def validate_dates(self):
        if self.created_at is not None and self.last_used_at is None:
            self.last_used_at = self.created_at

        elif self.last_used_at is not None and self.created_at is None:
            raise ValueError("Missing created_at")

        elif self.created_at is not None and self.last_used_at is not None:
            created_at_datetime = datetime.strptime(
                self.created_at, r"%Y-%m-%d %H:%M:%S"
            )
            last_used_at_datetime = datetime.strptime(
                self.last_used_at, r"%Y-%m-%d %H:%M:%S"
            )

            if created_at_datetime > last_used_at_datetime:
                raise ValueError("created_at cannot be greater than last_used_at")

        return self


class UserInDB(BaseModel):
    hashed_password: Optional[SecretStr] = Field(
        description="Hashed password stored in DB"
    )

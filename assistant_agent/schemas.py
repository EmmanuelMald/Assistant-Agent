from pydantic.functional_serializers import PlainSerializer
from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    SecretStr,
    BeforeValidator,
    AfterValidator,
)
from datetime import datetime
from typing import Optional, Annotated
import json


# Common Field Validators
STRING_NORMALIZER = BeforeValidator(
    lambda text: str(text).strip() if text is not None else None
)
UPPER_STRING = AfterValidator(lambda text: text.upper() if text is not None else None)


# Common fields
USER_ID_FIELD = Annotated[
    str,
    Field(
        default=None,  # In case this field is not included
        description="ID of the user",
        pattern=r"^UID\d{4}[A-Z0-9]{6}$",
    ),
    STRING_NORMALIZER,
]
CHAT_SESSION_ID_FIELD = Annotated[
    str,
    Field(
        default=None,
        description="ID of the user's chat session",
        pattern=r"^CS\d{4}[A-Z0-9]{6}-\d{3}$",
    ),
    STRING_NORMALIZER,
]
PROMPT_ID_FIELD = Annotated[
    str,
    Field(default=None, description="ID of the prompt.", pattern=r"^PID\d{13}-\d{4}$"),
    STRING_NORMALIZER,
]
CREATED_AT_FIELD = Annotated[
    datetime,
    Field(
        default=None,
        description="Datetime when a resource was created",
    ),
    PlainSerializer(  # Tells pydantic when serializing (converting to a dict or a json string), use the function
        lambda dt: dt.strftime(r"%Y-%m-%d %H:%M:%S"),
        when_used="always",
    ),
]


class User(BaseModel, validate_assignment=True):
    """
    This class will receive the data obtained when the user logs by the first time or
    when trying to login
    """

    user_id: USER_ID_FIELD
    created_at: CREATED_AT_FIELD
    full_name: Annotated[
        str,
        Field(
            description="Full name of the user",
            min_length=1,
        ),
        STRING_NORMALIZER,
        AfterValidator(lambda text: text.title()),
    ]
    company_name: Annotated[
        Optional[str],
        Field(
            default=None,  # Only in case this field is not passed
            description="Name of the company where the user works for",
            min_length=1,
        ),
        STRING_NORMALIZER,
        UPPER_STRING,
    ]
    email: Annotated[EmailStr, Field(description="User's email")]
    company_role: Annotated[
        Optional[str],
        Field(
            default=None,  # Only in case this field is not passed
            description="Role that the user has in the company where he's working on",
        ),
        STRING_NORMALIZER,
        UPPER_STRING,
    ]
    password: Annotated[
        SecretStr,
        Field(
            description="User's password. Must be at least 8 characters long.",
            min_length=8,
        ),
    ]


class ChatSession(BaseModel, validate_assignment=True):
    user_id: USER_ID_FIELD
    chat_session_id: CHAT_SESSION_ID_FIELD
    created_at: CREATED_AT_FIELD


class Prompt(BaseModel, validate_assignment=True):
    prompt_id: PROMPT_ID_FIELD
    created_at: CREATED_AT_FIELD
    chat_session_id: CHAT_SESSION_ID_FIELD
    prompt: Annotated[
        str,
        Field(
            description="User's prompt",
            min_length=1,
        ),
        STRING_NORMALIZER,
    ]
    response: Annotated[
        str,
        Field(description="Agent response"),
        STRING_NORMALIZER,
    ]


class AgentStep(BaseModel, validate_assignment=True):
    step_id: Annotated[
        str,
        Field(
            default=None,
            description="ID of the step",
            pattern=r"^AST\d+-\d{8}$",
        ),
        STRING_NORMALIZER,
    ]
    chat_session_id: CHAT_SESSION_ID_FIELD
    prompt_id: PROMPT_ID_FIELD
    created_at: CREATED_AT_FIELD
    step_data: Annotated[
        dict,
        Field(description="Dictionary with all the data related to the agent's step"),
        PlainSerializer(  # Tells pydantic when serializing (converting to a dict or a json string), use the function
            lambda dict_data: json.dumps(dict_data),
            when_used="always",
        ),
    ]

from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelMessage
import json


def prepare_to_read_chat_history(chat_history: str) -> list[ModelMessage]:
    """
    Convert a chat sessions that is obtained in a json string format into a list[ModelMessage]
    that the agent can read during chat sessions.

    Args:
        chat_history: str -> JSON string containing all the chat session history

    Returns:
        list[ModelMessage] -> List of ModelMessage objects that the agent can process
    """
    # Convert the JSON string into a list of dictionaries
    chat_history = json.loads(chat_history)

    # Validates the structure of the python objects
    chat_history = to_jsonable_python(chat_history)

    # Convert into a list of ModelMessage
    chat_history = ModelMessagesTypeAdapter.validate_python(chat_history)

    return chat_history


def prepare_to_send_chat_history(chat_history: bytes) -> str:
    """
    Prepare the chat session obtained from the agent chat session to be sent through an API

    Args:
        chat_history: bytes -> Chat history obtained from agent.run_sync.all_messages_json()

    Returns:
        str: str -> JSON string
    """
    chat_history_python_objects = json.loads(chat_history)

    chat_history_string = json.dumps(chat_history_python_objects)

    return chat_history_string

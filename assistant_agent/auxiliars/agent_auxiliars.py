from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelMessage


def prepare_to_read_chat_history(chat_history: list[dict]) -> list[ModelMessage]:
    """
    Convert a chat session history that is obtained as a list of dictionaries and
    transform it into a list[ModelMessage] that the agent can read during chat sessions.

    Args:
        chat_history: list[dict] -> list of dictionaries obtained fron the database, this contains all the
                                    agent steps, not only the answer/response

    Returns:
        list[ModelMessage] -> List of ModelMessage objects that the agent can process
    """

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

    return chat_history.decode("UTF-8")

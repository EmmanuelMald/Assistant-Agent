from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelMessage
import json


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


def get_new_agent_steps(previous_steps: list[dict], all_steps: bytes):
    """
    Process the previous_steps and the new one to store only the new history generated

    Args:
        previous_steps: list[dict] -> List of dictionaries, each dictionary is an agent step
                                        that was already stored in the database
        all_steps: bytes -> binary string obtained after making agent.all_messages_json()

    Returns: -> list[dict] -> List of the new agent steps generated
    """
    # Convert it into a list of dictionaries
    all_steps = json.loads(all_steps)

    number_new_steps = len(previous_steps) - len(all_steps)  # always a negative number

    new_steps = all_steps[number_new_steps:]

    return new_steps


def prepare_to_send_chat_history(chat_history: bytes) -> str:
    """
    Prepare the chat session obtained from the agent chat session to be sent through an API

    Args:
        chat_history: bytes -> Chat history obtained from agent.run_sync.all_messages_json()

    Returns:
        str: str -> JSON string
    """

    return chat_history.decode("UTF-8")

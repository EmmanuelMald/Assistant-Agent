from fastapi import FastAPI, HTTPException, status, Response, Depends
from fastapi.security import OAuth2PasswordRequestForm
from .auth_security import get_current_user_id_from_token
from loguru import logger
from app.backend.models import (
    AgentRequest,
    AgentResponse,
    TokenResponse,
    UserLoginRequest,
)
from assistant_agent.schemas import (
    User,
    AgentStep,
    ChatSession,
    Prompt,
)
from assistant_agent.agent import generate_agent_instance
from assistant_agent.utils.agent_auxiliars import (
    prepare_to_read_chat_history,
    get_new_agent_steps,
)
from assistant_agent.authentication import authenticate_user, create_access_token
from assistant_agent.database.tables.bigquery import (
    BQAgentStepsTable,
    BQChatSessionsTable,
    BQPromptsTable,
    BQUsersTable,
)
from assistant_agent.config import APIConfig


app = FastAPI()

api_config = APIConfig()

# Instanciate only once the database tables
agent_steps_table = BQAgentStepsTable()
chat_sessions_table = BQChatSessionsTable()
users_table = BQUsersTable()
prompts_table = BQPromptsTable()


@app.post(api_config.AGENT_REQUEST_ENDPOINT, response_model=AgentResponse)
async def agent_request(
    request: AgentRequest,
    current_user_id: str = Depends(get_current_user_id_from_token),
):
    logger.debug("Generating new agent instance...")
    agent = generate_agent_instance()

    logger.info(f"user_id: {current_user_id}")

    logger.info("Getting chat_session_id...")
    if request.chat_session_id is None:
        logger.info("Creating a new chat session...")
        chat_session_id = chat_sessions_table.generate_new_row(
            ChatSession(user_id=current_user_id)
        )
        logger.info(f"New chat_session_id generated: {chat_session_id}")
        logger.info("Starting a new chat history")
        previous_agent_steps = list()  # To start a new chat session

    else:
        chat_session_id = request.chat_session_id
        logger.info(f"chat session id found: {chat_session_id}")

        # if a chat_session_id was passed, then always get the history from BigQuery
        logger.info("Getting history from the database")

        # Get a list of dictionaries
        previous_agent_steps = agent_steps_table.get_chat_session_history(
            chat_session_id
        )
        logger.info("Chat history obtained from the database")

    # Convert it to a list of ModelRequest/ModelResponse objects
    chat_history = prepare_to_read_chat_history(previous_agent_steps)

    logger.info("Sending new prompt to the agent...")
    try:
        agent_answer = await agent.run(
            request.current_user_prompt, message_history=chat_history
        )
        logger.info(f"Agent response:{agent_answer.output}")

        logger.info("Storing prompt data...")
        prompt_data = Prompt(
            chat_session_id=chat_session_id,
            user_id=current_user_id,
            prompt=request.current_user_prompt,
            response=agent_answer.output,
        )
        prompt_id = prompts_table.generate_new_row(prompt_data=prompt_data)
        logger.info("Prompt data stored")

        logger.info("Storing agent steps...")

        # Get the history as a binary string
        all_agent_steps = agent_answer.all_messages_json()

        new_steps = get_new_agent_steps(
            previous_steps=previous_agent_steps,
            all_steps=all_agent_steps,
        )

        # prepare the steps to be stored in the DB
        new_steps_prepared = [
            AgentStep(
                chat_session_id=chat_session_id,
                prompt_id=prompt_id,
                step_data=new_step,
            )
            for new_step in new_steps
        ]
        agent_steps_table.store_prompt_steps(new_steps_prepared)
        logger.info("Agent steps stored in DB")

    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

    response = AgentResponse(
        agent_response=agent_answer.output,
        chat_session_id=chat_session_id,
    )

    return response


@app.post(
    api_config.CREATE_USER_ENDPOINT,
    status_code=status.HTTP_201_CREATED,
    response_model=TokenResponse,
)
def add_user(user_data: User, response: Response):
    logger.info(f"Request to register email: {user_data.email}")
    try:
        user_id = users_table.generate_new_row(user_data)
        response.headers["Location"] = f"/users/{user_id}"

        access_token_payload = {"sub": user_id}

        access_token = create_access_token(data=access_token_payload)
        logger.info(f"Access token created for the {user_id = }")

    except ValueError as ve:
        if "user is already registered" in str(ve).lower():
            logger.warning(f"Conflict during user registration: {ve}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
        else:
            logger.error(f"Invalid user data provided: {ve}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid data: {str(ve)}",
            )
    except Exception as e:
        # Any other exception
        logger.error(
            f"Unexpected error during user registration: {e}", exc_info=True
        )  # exc_info=True for traceback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while registering the user.",
        )

    return TokenResponse(access_token=access_token, username=user_data.full_name)


@app.post(
    api_config.LOGIN_ENDPOINT,
    response_model=TokenResponse,
)
async def login_for_access_token(auth_form: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate users with its email and password.,
    Oauth2PasswordRequestForm needs

    Args:
        login_data: Oauth2PasswordRequestForm -> Class to be used to allow authentication on /docs,
                                                 this class uses:
                        username -> maps to the email of the user
                        password -> password

    Returns:
        Access token if authentication is successfull
    """
    login_data = UserLoginRequest(email=auth_form.username, password=auth_form.password)

    logger.info(f"Login request for email: {login_data.email}")

    userdb = authenticate_user(email=login_data.email, password=login_data.password)

    if not userdb:
        logger.warning(
            f"Failed login for {login_data.email} - incorrect credentails or user does not exist"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_payload = {"sub": userdb.user_id}

    access_token = create_access_token(data=access_token_payload)

    logger.info("Successfull login")
    logger.info(f"Token generated for: {userdb.user_id}")

    return TokenResponse(access_token=access_token, username=userdb.full_name)


@app.get(api_config.CHAT_SESSIONS_ENDPOINT, response_model=list[ChatSession])
async def get_user_sessions(
    current_user_id: str = Depends(get_current_user_id_from_token),
):
    try:
        # get_users_sessions already has error handlers
        chat_sessions = chat_sessions_table.get_user_sessions(current_user_id)
        return chat_sessions
    except ValueError as ve:
        logger.warning(
            f"Value error getting the chat_session_ids for {current_user_id}"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception:
        logger.error(f"Error trying to get chat_session_ids for {current_user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve chat sessions",
        )


@app.get(api_config.CHAT_SESSION_HISTORY_ENDPOINT, response_model=list[Prompt])
async def get_chat_history(
    chat_session_id: str, current_user_id: str = Depends(get_current_user_id_from_token)
):
    try:
        prompts_list = prompts_table.get_prompts_from_user_session(
            user_id=current_user_id,
            chat_session_id=chat_session_id,
        )
        return prompts_list
    except ValueError as ve:
        logger.warning(
            f"Value error getting the history of the chat session: {chat_session_id}"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception:
        logger.error(
            f"Error trying to get the history from the chat session: {chat_session_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve the chat session history",
        )

from fastapi import FastAPI, HTTPException, status, Response, Depends
from fastapi.security import OAuth2PasswordRequestForm
from .auth_security import get_current_user_id_from_token
from loguru import logger
from app.backend.models import (
    AgentRequest,
    AgentResponse,
    UserRegistrationResponse,
    TokenResponse,
    UserLoginRequest,
    ChatSessionsResponse,
)
from assistant_agent.schemas import User, ChatSession, Prompt, AgentStep
from assistant_agent.agent import generate_agent_instance
from assistant_agent.auxiliars.agent_auxiliars import (
    prepare_to_read_chat_history,
    prepare_to_send_chat_history,
)
from assistant_agent.authentication import authenticate_user, create_access_token
from assistant_agent.database.tables.bigquery import (
    BQAgentStepsTable,
    BQChatSessionsTable,
    BQPromptsTable,
    BQUsersTable,
)
from assistant_agent.config import APIConfig
import json


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

    else:
        chat_session_id = request.chat_session_id
        logger.info(f"chat session id found: {chat_session_id}")

    logger.debug("Preparing chat history to be read by the agent...")
    if request.chat_history == "[]":
        logger.info("Empty chat session history... Getting history from the database")
        previous_chat_history = agent_steps_table.get_chat_session_history(
            chat_session_id
        )
        previous_chat_history_string = json.dumps(previous_chat_history)
        chat_history = prepare_to_read_chat_history(previous_chat_history_string)

    else:
        chat_history = prepare_to_read_chat_history(request.chat_history)

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

        # Get the history as a binary string
        new_chat_history_binary = agent_answer.all_messages_json()

        # Get the history as a string
        new_chat_history = prepare_to_send_chat_history(new_chat_history_binary)

        logger.info("Storing agent steps...")
        # Get a list of dictionaries
        full_history_steps = json.loads(new_chat_history)

        # Get the current history stored in the DB
        db_history = agent_steps_table.get_chat_session_history(chat_session_id)

        # Get the difference in the history between the database and the current history
        new_history = len(full_history_steps) - len(db_history)
        new_steps = full_history_steps[-new_history:]

        for new_step in new_steps:
            agent_step = AgentStep(
                chat_session_id=chat_session_id, prompt_id=prompt_id, step_data=new_step
            )
            agent_steps_table.generate_new_row(step_data=agent_step)
        logger.info("Agent steps stored in DB")

    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

    response = AgentResponse(
        agent_response=agent_answer.output,
        current_history=new_chat_history,
        chat_session_id=chat_session_id,
    )

    return response


@app.post(
    api_config.CREATE_USER_ENDPOINT,
    status_code=status.HTTP_201_CREATED,
    response_model=UserRegistrationResponse,
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

    return UserRegistrationResponse(
        user_id=user_id,
        access_token=access_token,
        username=user_data.full_name,
    )


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


@app.get(api_config.CHAT_SESSIONS_ENDPOINT, response_model=ChatSessionsResponse)
async def get_user_sessions(current_user_id=Depends(get_current_user_id_from_token)):
    # get_users_sessions already has error handlers
    chat_sessions = chat_sessions_table.get_user_sessions(current_user_id)
    return ChatSessionsResponse(sessions=chat_sessions)

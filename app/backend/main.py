from fastapi import FastAPI, HTTPException, status, Response
from loguru import logger
from app.backend.models import (
    AgentRequest,
    AgentResponse,
    UserRegistrationResponse,
    TokenResponse,
    UserLoginRequest,
)
from assistant_agent.schemas import User
from assistant_agent.agent import generate_agent_instance
from assistant_agent.database.tables.bigquery import BQUsersTable
from assistant_agent.auxiliars.agent_auxiliars import (
    prepare_to_read_chat_history,
    prepare_to_send_chat_history,
)
from assistant_agent.authentication import authenticate_user, create_access_token
from assistant_agent.config import APIConfig

app = FastAPI()

api_config = APIConfig()


@app.post(api_config.AGENT_REQUEST_ENDPOINT, response_model=AgentResponse)
async def agent_request(request: AgentRequest):
    logger.debug("Generating new agent instance...")
    agent = generate_agent_instance()
    logger.debug("Agent instance generated successfully")

    logger.debug("Preparing chat history to be read by the agent...")
    chat_history = prepare_to_read_chat_history(request.chat_history)
    logger.debug("History chat session prepared")

    logger.info("Sending new prompt to the agent...")
    try:
        agent_answer = await agent.run(
            request.current_user_prompt, message_history=chat_history
        )
        logger.info(f"Agent response:{agent_answer.output}")

    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

    new_chat_history_binary = agent_answer.all_messages_json()
    new_chat_history = prepare_to_send_chat_history(new_chat_history_binary)
    response = AgentResponse(
        agent_response=agent_answer.output, current_history=new_chat_history
    )

    return response


@app.post(
    api_config.CREATE_USER_ENDPOINT,
    status_code=status.HTTP_201_CREATED,
    response_model=UserRegistrationResponse,
)
def add_user(user_data: User, response: Response):
    logger.debug("Connecting to the database...")
    users_table = BQUsersTable()
    logger.debug("Users table successfully connected")

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

    return UserRegistrationResponse(user_id=user_id, access_token=access_token)


@app.post(
    api_config.LOGIN_ENDPOINT,
    response_model=TokenResponse,
)
async def login_for_access_token(login_data: UserLoginRequest):
    """
    Authenticate users with its email and password

    Args:
        user_data: UserLoginRequest -> Class containing all the data related to the login

    Returns:
        Access token if authentication is successfull
    """
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

    return TokenResponse(access_token=access_token)

from fastapi import FastAPI, HTTPException, status, Response
from loguru import logger
from app.backend.models import AgentRequest, AgentResponse, UserRegistrationResponse
from assistant_agent.schemas import User
from assistant_agent.agent import generate_agent_instance
from assistant_agent.database.tables.bigquery import BQUsersTable
from assistant_agent.auxiliars.agent_auxiliars import (
    prepare_to_read_chat_history,
    prepare_to_send_chat_history,
)

app = FastAPI()


@app.post("/ask_agent", response_model=AgentResponse)
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
    "/add_user",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRegistrationResponse,
)
def add_user(user_data: User, response: Response):
    logger.debug("Connecting to the database...")
    users_table = BQUsersTable()
    logger.debug("Users table successfully connected")

    try:
        user_id = users_table.generate_new_row(user_data)
        response.headers["Location"] = f"/users/{user_id}"

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

    message = "User registered successfully!"

    return UserRegistrationResponse(user_id=user_id, message=message)

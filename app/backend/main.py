from fastapi import FastAPI, HTTPException
from loguru import logger

import sys

sys.path.append("../..")

from app.backend.models import AgentRequest, AgentResponse
from assistant_agent.agent import generate_agent_instance
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
    logger.info("Preparing chat history to be read by the agent...")
    chat_history = prepare_to_read_chat_history(request.chat_history)
    logger.info("History chat session prepared")
    logger.info("Sending new prompt to the agent...")
    try:
        agent_answer = await agent.run(
            request.current_user_prompt, message_history=chat_history
        )
        logger.info(f"Agent response:{agent_answer.output}")

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

    new_chat_history_binary = agent_answer.all_messages_json()
    new_chat_history = prepare_to_send_chat_history(new_chat_history_binary)
    response = AgentResponse(
        agent_response=agent_answer.output, current_history=new_chat_history
    )

    return response

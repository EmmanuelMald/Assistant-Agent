import streamlit as st
from loguru import logger
import sys

sys.path.append("..")

from app.utils import find_image_urls
from assistant_agent.hello_agent import agent
from assistant_agent.config import LLMConfig

llm_config = LLMConfig()

MESSAGES_MEMORY_LIMIT = llm_config.AGENT_MESSAGES_MEMORY_LIMIT


def main():
    # Config of the streamlit interface
    st.title("Image Generation Agent")
    st.write("Ask the agent to generate images based on your ideas.")

    # Initialize session history if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # If the message is from the assistant and has image URLs, display them
            if (
                message["role"] == "assistant"
                and "image_urls" in message
                and message["image_urls"]
            ):
                for url in message["image_urls"]:
                    st.image(url, width=300)  # Adjust width as needed

    # Handle user input
    if prompt := st.chat_input("What image idea do you have?"):
        # Add user message to history and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get previous messages from the history
        user_messages = [
            msg["content"] for msg in st.session_state.messages if msg["role"] == "user"
        ]

        previous_user_prompts = user_messages[-(MESSAGES_MEMORY_LIMIT + 1) : -1]

        if previous_user_prompts:
            previous_requests_str = "\n\n".join(previous_user_prompts)

            full_request = f"{prompt}\n\nConsider the previous requests:\n\n{previous_requests_str}"
            logger.info(
                f"Sending request with memory. Previous prompts included: {len(previous_user_prompts)}"
            )

        else:
            full_request = prompt
        # Get response from the agent
        try:
            with st.spinner("Agent is thinking..."):
                logger.info(f"Running agent with input: '{prompt}'")
                result = agent.run_sync(full_request)
                response_text = result.output
                logger.info(f"Agent responded: '{response_text}'")

            # Find image URLs in the agent's response
            image_urls_found = find_image_urls(response_text)
            logger.info(f"Image URLs found in response: {image_urls_found}")

            # Add agent response to history (including found URLs)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response_text,
                    "image_urls": image_urls_found,  # Store found URLs
                }
            )

            # Display agent response in the UI
            with st.chat_message("assistant"):
                st.markdown(response_text)  # Display the full text
                # If URLs were found, display them as images
                if image_urls_found:
                    for url in image_urls_found:
                        st.image(url, width=300)  # Display each image

        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)
            error_message = f"Sorry, an error occurred: {e}"
            st.error(error_message)
            # Add error message to history
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message, "image_urls": []}
            )


if __name__ == "__main__":
    main()

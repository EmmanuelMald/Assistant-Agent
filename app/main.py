import streamlit as st
from loguru import logger
import re
import sys

sys.path.append("..")

from assistant_agent.hello_agent import agent

# Config of the streamlit interface
st.title("Image Generation Agent Interface")
st.write("Ask the agent to generate images based on your ideas.")


def find_image_urls(text: str) -> list[str]:
    """
    Finds potential image URLs within a given text string.

    Specifically targets URLs pointing to Google Cloud Storage (GCS)
    and ending with common image file extensions.

    Args:
        text: The text string to search within.

    Returns:
        A list of found image URLs (strings). Returns an empty list if none are found.
    """
    regex = r"(https://storage\.googleapis\.com/[^ ]+\.(?:png|jpg|jpeg|gif|webp|svg))"
    urls = re.findall(regex, text)
    return urls


# --- Streamlit UI Logic ---

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
# Use a more descriptive placeholder in the target language if desired
if prompt := st.chat_input(
    "What image idea do you have?"
):  # Changed placeholder to English
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from the agent
    try:
        with st.spinner("Agent is thinking..."):  # Spinner text in English
            logger.info(f"Running agent with input: '{prompt}'")
            # Assume 'agent' is the initialized pydantic-ai Agent object
            result = agent.run_sync(prompt)
            response_text = result.output  # The agent's text response
            logger.info(f"Agent responded: '{response_text}'")

        # --- Process response to display image ---
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
            # --------------------------------------

    except Exception as e:
        logger.error(f"Error during agent execution: {e}", exc_info=True)
        error_message = f"Sorry, an error occurred: {e}"  # Error message in English
        st.error(error_message)
        # Add error message to history
        st.session_state.messages.append(
            {"role": "assistant", "content": error_message, "image_urls": []}
        )
        # No need to display it again here, the main loop will handle it

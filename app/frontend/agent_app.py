import streamlit as st
from loguru import logger
import sys
import requests


sys.path.append("../..")


from assistant_agent.agent_auxiliars import find_image_urls
from app.frontend.config import BackendInfo


backend_config = BackendInfo()

ask_agent_url = backend_config.BASE_URL + backend_config.AGENT_REQUEST_ENDPOINT


def main():
    st.title("Image Generation Agent")
    st.write("Ask the agent to generate images based on your ideas.")

    # Visual chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    # History in the required format by the API
    if "formatted_chat_history" not in st.session_state:
        # Initializing an empty chat history
        st.session_state.formatted_chat_history = "[]"  # Required by the agent API

    # Show chat session history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if (
                message["role"] == "assistant"
                and "image_urls" in message
                and message["image_urls"]
            ):
                for url in message["image_urls"]:
                    st.image(url, width=300)

    # User input
    if prompt := st.chat_input("What image idea do you have?"):
        # Add user prompt in the visual chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare to send the request to the agent API
        try:
            with st.spinner("Agent is thinking..."):
                # Get the whole chat history
                previous_formatted_history = st.session_state.formatted_chat_history

                payload = {
                    "current_user_prompt": prompt,
                    "chat_history": previous_formatted_history,
                }

                # Calling the agent API
                response = requests.post(url=ask_agent_url, json=payload)

                # Process response
                if response.status_code == 200:
                    try:
                        response_data = response.json()

                        # Extract agent data
                        agent_response_text = response_data["agent_response"]
                        new_formatted_history = response_data["current_history"]

                        logger.info(f"Agent responded: '{agent_response_text}'")

                        # Update chat history formatted
                        st.session_state.formatted_chat_history = new_formatted_history

                        # Find image URLs that the agent retrieved
                        image_urls_found = find_image_urls(agent_response_text)
                        logger.info(f"Image URLs found: {image_urls_found}")

                        # Show agent response
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": agent_response_text,
                                "image_urls": image_urls_found,
                            }
                        )

                        # Force rerun just in case
                        st.rerun()

                    except requests.exceptions.JSONDecodeError:
                        logger.error(
                            f"Failed to decode JSON. Response text: {response.text}"
                        )
                        st.error(
                            "Error: Could not understand the response from the agent."
                        )
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": "Error: Invalid response format.",
                                "image_urls": [],
                            }
                        )
                    except KeyError as e:
                        logger.error(
                            f"Missing key in API JSON response: {e}. Response: {response.json()}"
                        )
                        st.error(
                            f"Error: Unexpected response structure from agent (missing {e})."
                        )
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": f"Error: Missing expected data from agent ({e}).",
                                "image_urls": [],
                            }
                        )

                # Process any API error
                else:
                    error_message = f"Error calling agent. Status: {response.status_code}. Details: {response.text}"
                    logger.error(error_message)
                    st.error(error_message)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f"Error from API: {response.status_code}",
                            "image_urls": [],
                        }
                    )

        # Handle network errors and others
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}", exc_info=True)
            error_message = f"Sorry, could not connect to the agent: {e}"
            st.error(error_message)
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message, "image_urls": []}
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            error_message = f"Sorry, an unexpected error occurred: {e}"
            st.error(error_message)
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message, "image_urls": []}
            )
        finally:
            # Update the UI after any unexpected error
            st.rerun()


if __name__ == "__main__":
    main()

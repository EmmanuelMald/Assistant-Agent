import streamlit as st
from loguru import logger
import requests
from app.frontend.utils import find_image_urls
from app.frontend.config import PagesConfig
from assistant_agent.config import APIConfig


backend_config = APIConfig()
pages_config = PagesConfig()


ask_agent_url = backend_config.BASE_URL + backend_config.AGENT_REQUEST_ENDPOINT

# --- Page protection and logout y Logout ---
st.set_page_config(
    page_title="Agent Chat", layout="wide", initial_sidebar_state="expanded"
)  # Mostrar sidebar para logout

hide_pages_nav_css = """
    <style>
        [data-testid="stSidebarNav"] { /* Este es el selector para la navegación de páginas */
            display: none;
        }
    </style>
"""
st.markdown(hide_pages_nav_css, unsafe_allow_html=True)

if not st.session_state.get("logged_in") or not st.session_state.get("access_token"):
    st.warning("Please login or register to access the agent chat")

    # Share links to register or to log in
    col1_nav, col2_nav = st.columns(2)
    with col1_nav:
        if st.button("Go to Login", key="chat_goto_login", use_container_width=True):
            st.switch_page(pages_config.login)
    with col2_nav:
        if st.button(
            "Go to Registration", key="chat_goto_reg", use_container_width=True
        ):
            st.switch_page(pages_config.registration)
    st.stop()  # Detener la ejecución de esta página si no está logueado


# Log out button in the lateral bar
with st.sidebar:
    first_name = st.session_state.get("user_full_name", "User").split()[0]
    st.write(f"Welcome, {first_name}!")
    if st.session_state.get("user_email"):
        st.caption(f"Email: {st.session_state.get('user_email')}")
    if st.session_state.get("user_id"):
        st.caption(f"UserID: {st.session_state.get('user_id')}")

    if st.button("Logout", key="logout_button_chat", use_container_width=True):
        logger.info(f"{first_name} logging out.")
        keys_to_clear = [
            "logged_in",
            "user_id",
            "user_full_name",
            "user_email",
            "access_token",
            "messages",
            "formatted_chat_history",
            "active_prompt",
            "processing_request",
            "registered_user_info",
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.success("You have been logged out.")
        st.switch_page(pages_config.login)  # Redirect to login page
# End of logout


st.title("Image Generation Agent")
st.write("Ask the agent to generate images based on your ideas.")


# Track if a prompt is being processed
if "processing_request" not in st.session_state:
    st.session_state.processing_request = False
# Temporal storage of the current prompt
if "active_prompt" not in st.session_state:
    st.session_state.active_prompt = None

# Visual chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
# History in the required format by the API
if "formatted_chat_history" not in st.session_state:
    # Initializing an empty chat history
    st.session_state.formatted_chat_history = "[]"  # Required by the agent API
if "chat_session_id" not in st.session_state:
    # Start with an empty session_id
    st.session_state.chat_session_id = None

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
user_prompt_input = st.chat_input(
    "What image idea do you have?", disabled=st.session_state.processing_request
)

if user_prompt_input and not st.session_state.processing_request:
    st.session_state.messages.append({"role": "user", "content": user_prompt_input})
    with st.chat_message("user"):  # Add user prompt in the visual chat history
        st.markdown(user_prompt_input)

    st.session_state.active_prompt = user_prompt_input  # Store prompt to process
    st.session_state.processing_request = True  # Set as processing prompt
    st.rerun()  # Update the input button to be disabled and start processing

# Processing prompt
if st.session_state.processing_request and st.session_state.active_prompt:
    prompt_to_process = st.session_state.active_prompt  # Get the prompt

    # Get the access token from the state of the session
    access_token = st.session_state.get("access_token")

    if not access_token:
        st.error("Authentication token not found, please log in again")
        logger.warning(
            "Attempted to process prompt but no access token found in session state"
        )

        st.session_state.processing_request = False
        st.session_state.active_prompt = None

        if st.button("Go to Login Page", key="token_missing_login_btn_chat"):
            st.switch_page(pages_config.login)
        st.stop()  # Stop if there is no token

    # Building the header
    headers = {"Authorization": f"Bearer {access_token}"}

    logger.debug(f"User prompt to process: {prompt_to_process}")

    try:
        with st.spinner("Agent is thinking..."):
            # Get the whole chat history
            previous_formatted_history = st.session_state.formatted_chat_history

            # Get the chat_session_id
            previous_chat_session_id = st.session_state.chat_session_id

            logger.debug("Chat history obtained")

            payload = {
                "current_user_prompt": prompt_to_process,
                "chat_history": previous_formatted_history,
                "chat_session_id": previous_chat_session_id,
            }
            logger.debug("Payload created")

            # Calling the agent API
            logger.info("Sending prompt to the agent...")
            response = requests.post(url=ask_agent_url, json=payload, headers=headers)

            # Process response
            if response.status_code == 200:
                try:
                    response_data = response.json()

                    # Extract agent data
                    agent_response_text = response_data["agent_response"]
                    new_formatted_history = response_data["current_history"]
                    new_chat_session_id = response_data["chat_session_id"]

                    logger.info(f"Agent responded: '{agent_response_text}'")

                    # Update chat history formatted
                    st.session_state.formatted_chat_history = new_formatted_history

                    # Update chat_sesion_id
                    st.session_state.chat_session_id = new_chat_session_id

                    # Find image URLs that the agent retrieved
                    image_urls_found = find_image_urls(agent_response_text)
                    logger.debug(f"Image URLs found: {image_urls_found}")

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
                    st.error("Error: Could not understand the response from the agent.")
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

            elif response.status_code == 401:  # Unauthorized - Invalid token or expired
                logger.warning(
                    f"Authentication error (401) when calling /ask_agent. Details: {response.text[:500]}"
                )
                st.error("Your session has expired or is invalid. Please log in again.")
                # Clear states to force login
                st.session_state.logged_in = False
                st.session_state.access_token = None

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
        # Clear all the states and rerun the UI
        st.session_state.processing_request = False
        st.session_state.active_prompt = None
        st.rerun()

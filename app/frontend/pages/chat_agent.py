import streamlit as st
from loguru import logger
import requests
from app.frontend.utils import find_image_urls
from app.frontend.config import PagesConfig
from assistant_agent.config import APIConfig


backend_config = APIConfig()
pages_config = PagesConfig()


ask_agent_url = backend_config.BASE_URL + backend_config.AGENT_REQUEST_ENDPOINT
chat_sessions_url = backend_config.BASE_URL + backend_config.CHAT_SESSIONS_ENDPOINT
chat_history_url = (
    backend_config.BASE_URL + backend_config.CHAT_SESSION_HISTORY_ENDPOINT
)

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
    st.stop()  # Stop execution if not logged

############ Initialize session variables #######################
# Track if a prompt is being processed
if "processing_request" not in st.session_state:
    st.session_state.processing_request = False
# Temporal storage of the current prompt
if "active_prompt" not in st.session_state:
    st.session_state.active_prompt = None
# Visual chat history
if "messages" not in st.session_state:
    st.session_state.messages = list()
if "chat_session_id" not in st.session_state:
    # Start with an empty session_id
    st.session_state.chat_session_id = None
if "user_chat_sessions" not in st.session_state:
    st.session_state.user_chat_sessions = list()
if "sessions_loaded" not in st.session_state:
    st.session_state.sessions_loaded = False  # Flag that controls the load

# Sidebar
with st.sidebar:
    first_name = st.session_state.get("user_full_name", "User").split()[0]
    st.write(f"Welcome, {first_name}!")

    if st.button(
        "New Chat",
        key="new_chat_button",
        use_container_width=True,
        disabled=st.session_state.processing_request,
    ):
        st.session_state.chat_session_id = None
        st.session_state.messages = list()
        st.session_state.session_loaded = False
        st.rerun()

    st.markdown("---")

    if not st.session_state.sessions_loaded and st.session_state.access_token:
        # Setting the user sessions
        headers = {"Authorization": f"bearer {st.session_state.access_token}"}
        sessions_response = requests.get(chat_sessions_url, headers=headers)

        if sessions_response.status_code == 200:
            sessions_data = sessions_response.json()
            st.session_state.user_chat_sessions = [
                session_data["chat_session_id"] for session_data in sessions_data
            ]
            st.session_state.sessions_loaded = True

    if len(st.session_state.user_chat_sessions) > 0:
        st.write("Chat Sessions:")
        for session_number, session_id in enumerate(
            st.session_state.user_chat_sessions
        ):
            if st.button(
                f"Session {session_id}",
                key=f"session_button_{session_number}",
                use_container_width=True,
                disabled=st.session_state.processing_request,
            ):
                headers = {"Authorization": f"bearer {st.session_state.access_token}"}
                # Save the chat_session_id in the state of the session
                st.session_state.chat_session_id = session_id
                # Reset the messages in the UI to show only the current history
                st.session_state.messages = list()

                # Retrieve the chat session history
                chat_history_url = chat_history_url.replace(
                    "{chat_session_id}", st.session_state.chat_session_id
                )
                session_history_response = requests.get(
                    chat_history_url, headers=headers
                )

                session_history = session_history_response.json()
                session_messages = []

                # Prepare the messages to be displayed in the UI
                for message in session_history:
                    user_message = {"role": "user", "content": message["prompt"]}
                    assistant_message = {
                        "role": "assistant",
                        "content": message["response"],
                        "image_urls": find_image_urls(message["response"]),
                    }
                    session_messages.append(user_message)
                    session_messages.append(assistant_message)

                # Store all the session messages in the session state to be displayed in the UI
                st.session_state.messages = session_messages
                st.rerun()

    else:
        st.write("No sessions yet")

    st.markdown("---")
    if st.session_state.get("user_email"):
        st.caption(f"Email: {st.session_state.get('user_email')}")

    # Log out button in the lateral bar
    if st.button(
        "Logout",
        key="logout_button_chat",
        use_container_width=True,
        disabled=st.session_state.processing_request,
    ):
        logger.info(f"{first_name} logging out.")
        keys_to_clear = [
            "logged_in",
            "user_full_name",
            "user_email",
            "access_token",
            "messages",
            "chat_session_id",
            "active_prompt",
            "processing_request",
            "user_chat_sessions",
            "sessions_loaded",
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.success("You have been logged out.")
        st.switch_page(pages_config.login)  # Redirect to login page
# End of logout


st.title("Image Generation Agent")
st.write("Ask the agent to generate images based on your ideas.")


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
                st.image(url, width=600)

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
            # Get the chat_session_id
            previous_chat_session_id = st.session_state.chat_session_id

            logger.debug("Chat history obtained")

            payload = {
                "current_user_prompt": prompt_to_process,
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
                    new_chat_session_id = response_data["chat_session_id"]

                    logger.info(f"Agent responded: '{agent_response_text}'")

                    if (
                        previous_chat_session_id is None
                        and new_chat_session_id is not None
                    ):
                        st.session_state.sessions_loaded = False
                        logger.info("New chat session created, reloading sessions")

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

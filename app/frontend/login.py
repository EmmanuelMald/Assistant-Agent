# app/frontend/pages/login_page.py
import streamlit as st
import requests
from loguru import logger
import sys
from app.frontend.config import PagesConfig
from assistant_agent.config import APIConfig


# Logger configuration
if "logger_configured_login_page" not in st.session_state:
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    st.session_state.logger_configured_login_page = True

backend_config = APIConfig()
pages_config = PagesConfig()

# URL para el endpoint de login
login_url = backend_config.BASE_URL + backend_config.LOGIN_ENDPOINT


st.set_page_config(page_title="Login - Agent App", layout="centered")


hide_sidebar_and_toggle_button_css = """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        button[data-testid="stSidebarNavToggler"] {
            display: none;
        }
    </style>
"""
st.markdown(hide_sidebar_and_toggle_button_css, unsafe_allow_html=True)


# Redirect if already logged in
if st.session_state.get("logged_in") and st.session_state.get("access_token"):
    logger.info("User already logged, redirecting to the chat page from the login.")
    st.switch_page(pages_config.chat_agent)


st.title("Login to Your Account")
st.write("Access the Image Generation Agent.")

with st.form("login_form_on_page", clear_on_submit=False):
    st.subheader("Enter your credentials:")
    login_email = st.text_input("Email", key="login_page_email")
    login_password = st.text_input("Password", type="password", key="login_page_pwd")

    login_submitted = st.form_submit_button("Login")

    if login_submitted:
        if not login_email or not login_password:
            st.error("Please enter both email and password.")
        else:
            logger.info(f"Login attempt for user (email as username): {login_email}")

            # Payload to load  as form-data (application/x-www-form-urlencoded)
            payload_for_form_data = {
                "username": login_email,
                "password": login_password,
            }

            try:
                # Using 'data' paramater to send as form-data
                response = requests.post(
                    login_url, data=payload_for_form_data, timeout=10
                )

                if response.status_code == 200:  # Login exitoso
                    login_response_data = response.json()

                    logger.debug("Token obtained")
                    access_token = login_response_data.get("access_token")
                    token_type = login_response_data.get("token_type", "bearer")
                    user_full_name = login_response_data.get("username")

                    if access_token:
                        st.success("Login successful! Redirecting to chat...")
                        logger.info(
                            f"User {login_email} logged in successfully. Token type: {token_type}"
                        )

                        # Almacenar información de sesión
                        st.session_state.logged_in = True
                        st.session_state.access_token = access_token
                        st.session_state.user_email = login_email
                        st.session_state.user_full_name = user_full_name
                        logger.debug("Token stored in session_state")

                        st.rerun()  # Para forzar la redirección por la condición al inicio de la página
                    else:
                        st.error(
                            "Login successful, but no access token was received from the server."
                        )
                        logger.error(
                            f"Login para {login_email} exitoso pero sin token en la respuesta: {login_response_data}"
                        )

                elif (
                    response.status_code == 401
                ):  # Unauthorized (credenciales incorrectas)
                    st.error(
                        response.json().get(
                            "detail", "Invalid email or password. Please try again."
                        )
                    )
                    logger.warning(
                        f"Failed login attempt for {login_email}: Incorrect credentials."
                    )
                elif (
                    response.status_code == 422
                ):  # Error de validación (ej. formato de email incorrecto)
                    error_detail = response.json().get("detail", "Invalid data format.")
                    if isinstance(error_detail, list):
                        messages = [
                            f"Field '{err.get('loc', ['?'])[-1]}': {err.get('msg', 'invalid')}"
                            for err in error_detail
                        ]
                        st.error(f"Login failed: {' '.join(messages)}")
                    else:
                        st.error(f"Login failed: {error_detail}")
                    logger.warning(
                        f"Login validation error for {login_email}: {response.json()}"
                    )
                else:  # Otros errores del servidor
                    st.error(
                        f"Login failed. Server responded with {response.status_code}: {response.text}"
                    )
                    logger.error(
                        f"Login server error for {login_email}: {response.status_code} - {response.text}"
                    )

            except requests.exceptions.Timeout:
                st.error(
                    "The login service took too long to respond. Please try again later."
                )
                logger.error(f"Timeout during login for {login_email} at {login_url}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the login service: {e}")
                logger.error(
                    f"Login connection error for {login_email}: {e}", exc_info=True
                )
            except Exception as e:  # Captura general
                st.error(f"An unexpected error occurred during login: {e}")
                logger.error(
                    f"Login unexpected error for {login_email}: {e}", exc_info=True
                )

st.markdown("---")
st.write("Don't have an account yet?")

# Button to fo to registration
if st.button("Register Here", key="goto_reg_btn_from_login"):
    st.switch_page(pages_config.registration)

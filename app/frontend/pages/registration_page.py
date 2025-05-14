import streamlit as st
import requests
from loguru import logger
import sys
from app.frontend.config import PagesConfig
from assistant_agent.config import APIConfig


if "logger_level_configured" not in st.session_state:
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    st.session_state.logger_level_configured = True


backend_config = APIConfig()
pages_config = PagesConfig()

add_user_url = backend_config.BASE_URL + backend_config.CREATE_USER_ENDPOINT


st.set_page_config(
    page_title="Register - Agent App",
    layout="centered",
    initial_sidebar_state="collapsed",
)

hide_entire_sidebar_css = """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
"""
st.markdown(hide_entire_sidebar_css, unsafe_allow_html=True)

# Si el usuario ya está logueado, redirigir al chat directamente
if st.session_state.get("logged_in") and st.session_state.get("access_token"):
    logger.info("Logged user, redirecting to chat")
    st.switch_page(pages_config.chat_agent)

st.title("Welcome! Register to use the service")
st.write("Create a new account to access the Image Generation Agent.")

with st.form("registration_form_main", clear_on_submit=False):
    st.subheader("Enter your details:")
    reg_full_name = st.text_input("Full Name*", key="main_reg_fn")
    reg_company_name = st.text_input("Company Name (Optional)", key="main_reg_cn")
    reg_company_role = st.text_input("Your Role (Optional)", key="main_reg_cr")
    reg_email = st.text_input("Email*", key="main_reg_email")
    reg_password = st.text_input("Password*", type="password", key="main_reg_pwd")
    reg_confirm_password = st.text_input(
        "Confirm Password*", type="password", key="main_reg_confirm_pwd"
    )

    submitted = st.form_submit_button("Register Account")

    if submitted:
        if not all([reg_full_name, reg_email, reg_password, reg_confirm_password]):
            st.error("Please fill in all mandatory fields (*).")
        elif reg_password != reg_confirm_password:
            st.error("Passwords do not match. Please re-enter.")
            logger.warning(f"Password mismatch during registration for: {reg_email}")
        else:
            payload = {
                "full_name": reg_full_name,
                "company_name": reg_company_name if reg_company_name else None,
                "company_role": reg_company_role if reg_company_role else None,
                "email": reg_email,
                "password": reg_password,
            }
            logger.info(f"Attempting registration for: {reg_email}")
            try:
                response = requests.post(add_user_url, json=payload, timeout=15)
                if response.status_code == 201:
                    response_data = response.json()
                    user_id = response_data.get("user_id")
                    access_token = response_data.get("access_token")
                    token_type = response_data.get("token_type")

                    st.success(
                        f"User '{reg_full_name}' registered successfully! Redirecting to chat..."
                    )
                    logger.info(f"User {reg_email} registered with ID {user_id}")

                    # Storing session info
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.user_full_name = reg_full_name
                    st.session_state.user_email = reg_email
                    st.session_state.access_token = access_token

                    st.balloons()
                    st.rerun()  # To force the verification of the login at the beginning and switch page

                elif response.status_code == 409:
                    st.error(
                        response.json().get(
                            "detail", "This email is already registered."
                        )
                    )
                elif response.status_code == 422:
                    error_detail = response.json().get("detail", "Invalid data.")
                    if isinstance(error_detail, list):
                        messages = [
                            f"Field '{err.get('loc', ['?'])[-1]}': {err.get('msg', 'invalid')}"
                            for err in error_detail
                        ]
                        st.error(f"Registration failed: {' '.join(messages)}")
                    else:
                        st.error(f"Registration failed: {error_detail}")
                else:
                    st.error(f"Server error: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")
                logger.error(f"Registration connection error for {reg_email}: {e}")

st.markdown("---")
st.write("Already have an account?")
# st.page_link crea un enlace visible y navegable
if st.button(
    "Login Here", key="goto_login_btn"
):  # Usamos un botón para más control o st.page_link
    st.switch_page(pages_config.login)

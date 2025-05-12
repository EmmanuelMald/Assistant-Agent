from pydantic_settings import BaseSettings


class PagesConfig(BaseSettings):
    chat_agent: str = "pages/chat_agent.py"
    login: str = "login.py"
    registration: str = "pages/registration_page.py"

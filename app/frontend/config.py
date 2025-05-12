from pydantic_settings import BaseSettings


class PagesConfig(BaseSettings):
    chat_agent: str = "pages/chat_agent.py"
    login: str = "pages/login.py"
    registration: str = "registration_page.py"

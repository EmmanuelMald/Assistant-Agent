from functools import lru_cache
import sys

sys.path.append("..")

from assistant_agent.config import GCPConfig, LLMConfig, AuthConfig
from assistant_agent.utils.gcp.secret_manager import get_secret

gcp_config = GCPConfig()
llm_config = LLMConfig()
auth_config = AuthConfig()


@lru_cache()
def get_llm_config() -> LLMConfig:
    """
    Get the LLMConfig class
    """
    secret_id = llm_config.SECRET_ID
    version_id = llm_config.SECRET_VERSION
    api_key = get_secret(secret_id, version_id, gcp_config.PROJECT_ID)

    return LLMConfig(API_KEY=api_key)


@lru_cache()
def get_auth_config() -> AuthConfig:
    """
    Get the AuthConfig class
    """
    secret_id = auth_config.SECRET_ID
    version_id = auth_config.SECRET_VERSION
    secret_key = get_secret(secret_id, version_id, gcp_config.PROJECT_ID)

    return AuthConfig(SECRET_KEY=secret_key)

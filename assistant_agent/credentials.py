from functools import lru_cache
import sys

sys.path.append("..")

from assistant_agent.config import GCPConfig, LLMConfig
from assistant_agent.utils.gcp.secret_manager import get_secret

gcp_config = GCPConfig()
llm_config = LLMConfig()


@lru_cache()
def get_llm_config() -> LLMConfig:
    """
    Get the LLMConfig with secret info
    """
    secret_id = llm_config.SECRET_ID
    version_id = llm_config.SECRET_VERSION
    api_key = get_secret(secret_id, version_id, gcp_config.PROJECT_ID)

    return LLMConfig(API_KEY=api_key)

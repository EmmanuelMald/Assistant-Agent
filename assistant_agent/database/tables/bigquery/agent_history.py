from assistant_agent.database.tables.bigquery import BigQueryTable, BQPromptsTable
from assistant_agent.config import GCPConfig

gcp_config = GCPConfig()


class AgentHistory(BigQueryTable):
    __name: str = gcp_config.AGENT_STEPS_TABLE_NAME
    __primary_key: str = gcp_config.AGENT_STEPS_TABLE_PK

    def __init__(self):
        super().__init__()
        self._prompts_table: BQPromptsTable = BQPromptsTable()

    @property
    def name(self):
        return self.__name

    @property
    def primary_key(self):
        return self.__primary_key

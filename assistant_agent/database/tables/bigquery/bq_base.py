from assistant_agent.database.tables.base import Table
from assistant_agent.config import GCPConfig

gcp_config = GCPConfig()


class BigQueryTable(Table):
    __project_id: str = gcp_config.PROJECT_ID
    __dataset_id: str = gcp_config.BQ_DATASET_ID

    @property
    def project_id(self):
        return self.__project_id

    @property
    def dataset_id(self):
        return self.__dataset_id

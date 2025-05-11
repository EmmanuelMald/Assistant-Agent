from assistant_agent.database.tables.bigquery.bq_base import BigQueryTable
from assistant_agent.database.tables.bigquery.users import BQUsersTable
from assistant_agent.utils.gcp.bigquery import query_data
from assistant_agent.config import GCPConfig
import re
from loguru import logger

gcp_config = GCPConfig()


class BQChatSessionsTable(BigQueryTable):
    __name: str = gcp_config.CHAT_SESSIONS_TABLE_NAME
    __primary_key: str = gcp_config.CHAT_SESSIONS_TABLE_PK

    def __init__(self):
        super().__init__()
        _users_table: str = BQUsersTable()

    @property
    def name(self) -> str:
        return self.__name

    @property
    def primary_key(self) -> str:
        return self.__primary_key

    def _generate_id(self, user_id: str) -> str:
        """
        Generates a new chat session id based on the current users registered in the DB

        Args:
            user_id: str -> Id of the user

        Returns:
            chat_session_id: str -> ID of the chat session generated

        """
        if not self._users_table.user_exists(user_id):
            raise ValueError("The user_id inserted is not valid")

        query = f"""
                select
                    count(*) as total_sessions
                from {self.project_id}.{self.dataset_id}.{self.name}
                where user_id = '{user_id}'
                """

        # Query the BigQuery database to get the total number of sessions of the user
        row_iterator = query_data(query=query)

        total_user_sessions = next(row_iterator).total_sessions

        # Generating the user ID
        next_id = total_user_sessions + 1

        # Extracting the user number from the user_id to generate a session_id
        match = re.search(r"\d+", user_id)
        user_number = int(match.group(0))

        chat_session_id = f"CSID{user_number}-{next_id:03d}"
        logger.info(f"Generated chat session ID: {chat_session_id}")

        return chat_session_id

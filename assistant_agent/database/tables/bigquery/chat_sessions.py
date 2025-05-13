from .bq_base import BigQueryTable
from assistant_agent.database.tables.bigquery import BQUsersTable
from assistant_agent.schemas import ChatSession, ChatSessionData
from assistant_agent.utils.gcp.bigquery import query_data, insert_rows
from assistant_agent.config import GCPConfig
import re
from datetime import datetime
from loguru import logger

gcp_config = GCPConfig()


class BQChatSessionsTable(BigQueryTable):
    __name: str = gcp_config.CHAT_SESSIONS_TABLE_NAME
    __primary_key: str = gcp_config.CHAT_SESSIONS_TABLE_PK

    def __init__(self):
        super().__init__()
        self._users_table: BQUsersTable = BQUsersTable()

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
            raise ValueError("The user_id does not exists")

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

    def session_exists(self, chat_session_id: str) -> bool:
        """
        Public method to know if a chat_session_id exists in the
        BigQuery table.

        Args:
            chat_session_id: str -> Id of the chat session

        Returns:
            bool -> True if the session exists, False otherwise
        """
        logger.info("Verifying if the chat session is already registered...")
        id_exists = super()._id_in_table(
            primary_key_row_value=chat_session_id,
            primary_key_column_name=self.primary_key,
            table_name=self.name,
        )

        return id_exists

    def _insert_row(self, session_info: ChatSession) -> str:
        """
        Insert chat session data into the BigQuery database.

        Args:
            chat_session_info: ChatSession -> Class containing the chat session info

        Returns:
            chat_session_id: str -> Id of the chat session generated
        """
        # _generate_id already has error handlers for the user_id
        logger.info("Generating chat_session_id...")
        chat_session_id = self._generate_id(session_info.user_id)
        logger.info(f"{chat_session_id = }")

        logger.info("Inserting data...")

        # Get the current date and time
        now = datetime.now()
        current_time = now.strftime(r"%Y-%m-%d %H:%M:%S")

        # Preparing the columns to fill in the BigQuery table
        data_to_insert = {
            "chat_session_id": chat_session_id,
            "user_id": session_info.user_id,
            "created_at": current_time,
        }

        try:
            insert_rows(
                table_name=self.name,
                dataset_name=self.dataset_id,
                project_id=self.project_id,
                rows=[
                    data_to_insert,
                ],
            )
        except Exception as e:
            raise ValueError(
                f"Error while inserting chat session's data into BigQuery: {e}"
            )

        return chat_session_id

    def generate_new_row(self, session_info: ChatSession) -> str:
        """
        Public method to generate a new row in the chat sessions table

        Args:
            session_info: ChatSession -> Info related to the session

        Returns:
            chat_session_id: str -> Id of the chat session generated
        """
        return self._insert_row(session_info)

    def get_user_sessions(self, user_id: str) -> list[ChatSessionData]:
        """
        Returns all the chat_session_ids of a user_id

        Args:
            user_id: Id of the user

        Returns:
            list[ChatSessionData] -> list of chat_sessions
        """
        logger.info("Validating user_id")
        userdb = self._users_table.user_exists(user_id)
        if not userdb:
            raise ValueError("The user_id does not exist")

        query = f"""
            select
                chat_session_id,
                created_at
            from {self.project_id}.{self.dataset_id}.{self.name}
            where user_id = '{user_id}'
            order by chat_session_id asc
        """

        rows_iterator = query_data(query)

        chat_sessions_info = [
            ChatSessionData(
                user_id=user_id,
                chat_session_id=row.chat_session_id,
                created_at=row.created_at,
            )
            for row in rows_iterator
        ]

        return chat_sessions_info

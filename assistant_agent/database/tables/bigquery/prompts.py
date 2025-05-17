from .bq_base import BigQueryTable
from assistant_agent.database.tables.bigquery import (
    BQUsersTable,
    BQChatSessionsTable,
)
from assistant_agent.utils.gcp.bigquery import insert_rows, query_data
from assistant_agent.config import GCPConfig
from assistant_agent.schemas import Prompt
from loguru import logger
from datetime import datetime, timezone

gcp_config = GCPConfig()


class BQPromptsTable(BigQueryTable):
    __name: str = gcp_config.PROMPTS_TABLE_NAME
    __primary_key: str = gcp_config.PROMPTS_TABLE_PK

    def __init__(self):
        super().__init__()
        self._users_table: BQUsersTable = BQUsersTable()
        self._chat_sessions_table: BQChatSessionsTable = BQChatSessionsTable()

    @property
    def name(self):
        return self.__name

    @property
    def primary_key(self):
        return self.__primary_key

    def _generate_id(self, chat_session_id: str) -> str:
        """
        Generates a prompt_id based on the user_id and chat_session_id

        Args:
            chat_session_id: str -> ID of the chat session of the user
        """
        if not self._chat_sessions_table.session_exists(chat_session_id):
            raise ValueError("Chat Session ID does not exist")

        # Get the last prompt number generated
        query = f"""
                select
                    count(*) as total_session_prompts
                from {self.project_id}.{self.dataset_id}.{self.name}
                where chat_session_id = '{chat_session_id}'
                """

        # Query the DB to get the number of prompts the chat_session_id has
        rows_iterator = query_data(query)

        total_session_prompts = next(rows_iterator).total_session_prompts

        # Generating the user ID
        next_id = total_session_prompts + 1

        # Extract the first coincidence of the regular expression
        session_number = chat_session_id[2:].repace("-", "")

        prompt_id = f"PID{session_number}-{next_id:04d}"
        logger.info(f"{prompt_id = }")

        return prompt_id

    def prompt_exists(self, prompt_id: str) -> bool:
        """
        Public method to know if a prompt exists in the DB

        Args:
            prompt_id -> ID of the prompt

        Returns:
            bool -> True if the prompt exists, otherwise False
        """
        id_exists = super()._id_in_table(
            primary_key_column_name=self.primary_key,
            primary_key_row_value=prompt_id,
            table_name=self.name,
        )

        return id_exists

    def _insert_row(self, prompt_data: Prompt) -> str:
        """
        Insert a row in the BigQuery table

        Args:
            prompt_data: Prompt -> Class with all the prompt info

        Return:
            str -> prompt_id
        """
        logger.info("Generating prompt_id...")

        # _generate_id() already has error handers for its inputs
        prompt_data.prompt_id = self._generate_id(prompt_data.chat_session_id)
        logger.info(f"prompt_id ={prompt_data.prompt_id}")

        logger.info("Inserting data...")

        prompt_data.created_at = datetime.now(timezone.utc)

        try:
            insert_rows(
                table_name=self.name,
                dataset_name=self.dataset_id,
                project_id=self.project_id,
                rows=[
                    prompt_data.model_dump(),
                ],
            )
        except Exception as e:
            raise ValueError(f"Error while inserting prompt's data into BigQuery: {e}")

        return prompt_data.prompt_id

    def generate_new_row(self, prompt_data: Prompt) -> str:
        """
        Public method to generate a new row in the prompts table

        Args:
            prompt_data: Prompt -> Class with all the prompt info

        Return:
            str -> prompt_id
        """
        return self._insert_row(prompt_data)

    def get_prompts_from_user_session(
        self, user_id: str, chat_session_id: str
    ) -> list[Prompt]:
        """
        Returns all the prompt data of a chat session id

        Args:
            chat_session_id: str -> Id of the chat session
            user_id: str -> Id of the user

        Returns:
            list[PromptData] -> Each entry is a prompt, containing the prompt,
                                response, and when it was creaetd
        """
        if not self._users_table.user_exists(user_id):
            raise ValueError("The user_id introduced does not exists")

        if not self._chat_sessions_table.session_exists(chat_session_id):
            raise ValueError("The chat_session_id does not exists")

        logger.info(
            "Verifying that the chat session owner corresponds to the user_id provided"
        )
        chat_session_owner_query = f"""
            select
                user_id
            from {self.project_id}.{self.dataset_id}.{self._chat_sessions_table.name}
            where {self._chat_sessions_table.primary_key} = '{chat_session_id}'
        """

        rows_iterator = query_data(chat_session_owner_query)

        chat_session_owner = next(rows_iterator).user_id

        if chat_session_owner != user_id:
            raise ValueError("The chat session is not of the user_id provided")

        # Getting the chat session historu
        query = f"""
                select
                    prompt_id,
                    chat_session_id,
                    created_at,
                    prompt,
                    response
                from {self.project_id}.{self.dataset_id}.{self.name}
                where chat_session_id = '{chat_session_id}'
                order by prompt_id asc
            """

        rows_iterator = query_data(query)

        total_prompts = [
            Prompt(
                prompt_id=row.prompt_id,
                chat_session_id=row.chat_session_id,
                created_at=row.created_at,
                prompt=row.prompt,
                response=row.response,
            )
            for row in rows_iterator
        ]

        return total_prompts

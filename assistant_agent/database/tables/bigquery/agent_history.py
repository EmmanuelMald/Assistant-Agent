from .bq_base import BigQueryTable
from assistant_agent.database.tables.bigquery import BQPromptsTable, BQChatSessionsTable
from assistant_agent.config import GCPConfig
from assistant_agent.utils.gcp.bigquery import query_data, insert_rows
from assistant_agent.schemas import AgentStep
from loguru import logger
import re

gcp_config = GCPConfig()


class BQAgentStepsTable(BigQueryTable):
    __name: str = gcp_config.AGENT_STEPS_TABLE_NAME
    __primary_key: str = gcp_config.AGENT_STEPS_TABLE_PK

    def __init__(self):
        super().__init__()
        self._prompts_table: BQPromptsTable = BQPromptsTable()
        self._sessions_table: BQChatSessionsTable = BQChatSessionsTable()

    @property
    def name(self):
        return self.__name

    @property
    def primary_key(self):
        return self.__primary_key

    def _generate_id(self, prompt_id: str, chat_session_id: str) -> str:
        """
        Generate an agent_step_id

        Args:
            prompt_id: str -> ID of the prompt that generated the step
            chat_session_id: str -> ID of the chat session where the prompt_id belongs to

        Returns:
            str -> agent_step_id
        """
        if not self._prompts_table.prompt_exists(prompt_id):
            raise ValueError("The prompt_id does not exist")

        if not self._sessions_table.session_exists(chat_session_id):
            raise ValueError("The chat_session_id does not exist")

        query = f"""
                select
                    count(*) as total_session_steps
                from {self.project_id}.{self.dataset_id}.{self.name}
                where chat_session_id = '{chat_session_id}'
                """

        # Query the BigQuery database to get the total number of sessions of the user
        row_iterator = query_data(query=query)

        session_steps = next(row_iterator).total_session_steps

        # Generate the step_id
        next_id = session_steps + 1

        # Extracting the prompt number from the prompt_id to generate a step_id
        match = re.search(r"\d+", prompt_id)
        prompt_number = int(match.group(0))

        step_id = f"AST{prompt_number}-{next_id:08d}"
        logger.info(f"{step_id = }")

        return step_id

    def step_exists(self, step_id: str) -> bool:
        """
        Public method to know if a step_id exists in the
        BigQuery table.

        Args:
            step_id: str -> Id of the step

        Returns:
            bool -> True if the step exists, False otherwise
        """
        logger.info("Verifying if the step_id is already registered...")
        id_exists = super()._id_in_table(
            primary_key_column_name=self.primary_key,
            primary_key_row_value=step_id,
            table_name=self.name,
        )

        return id_exists

    def _insert_row(self, step_data: AgentStep):
        """
        Insert the data related to the agent step into BigQuery

        Args:
            step_data: AgentStep -> Info related to the step

        Returns:
            str -> step_id
        """
        logger.info("Generating step_id...")
        # _generate_id has error handlers for its parameters
        step_id = self._generate_id(
            prompt_id=step_data.prompt_id,
            chat_session_id=step_data.chat_session_id,
        )

        logger.info("Inserting data...")

        data_to_insert = {
            "step_id": step_id,
            "chat_session_id": step_data.chat_session_id,
            "prompt_id": step_data.prompt_id,
            "step_data": step_data.step_data,
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
            raise ValueError(f"Error while inserting prompt's data into BigQuery: {e}")

        return step_id

    def generate_new_row(self, step_data: AgentStep):
        """
        Public method to generate a new row in the agent_steps table

        Args:
            step_data: AgentStep -> Info related to the step

        Returns:
            str -> step_id
        """
        return self._insert_row(step_data)

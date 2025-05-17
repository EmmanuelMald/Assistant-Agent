from .bq_base import BigQueryTable
from assistant_agent.database.tables.bigquery import BQPromptsTable, BQChatSessionsTable
from assistant_agent.config import GCPConfig
from assistant_agent.utils.gcp.bigquery import query_data, insert_rows
from assistant_agent.schemas import AgentStep
from datetime import datetime, timezone
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

    def _generate_id(self, prompt_id: str) -> str:
        """
        Generate an agent_step_id

        Args:
            prompt_id: str -> ID of the prompt that generated the step

        Returns:
            str -> agent_step_id
        """
        if not self._prompts_table.prompt_exists(prompt_id):
            raise ValueError("The prompt_id does not exist")

        query = f"""
                select
                    count(*) as total_prompt_steps
                from {self.project_id}.{self.dataset_id}.{self.name}
                where prompt_id = '{prompt_id}'
                """

        # Query the BigQuery database to get the total number of steps in the prompt
        row_iterator = query_data(query=query)

        prompt_steps = next(row_iterator).total_prompt_steps

        # Generate the step_id
        next_id = prompt_steps + 1

        # Extract the first numbers of the prompt_id
        prompt_number = prompt_id[3:].replace("-", "")

        step_id = f"AST{prompt_number}-{next_id:03d}"
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

    def _insert_row(self, step_data: AgentStep) -> None:
        """
        Insert the data related to the agent step into BigQuery, it
        suppose that all the step_data is correctly set

        Args:
            step_data: AgentStep -> Info related to the step

        Returns:
            None
        """
        logger.info("Inserting data...")

        try:
            insert_rows(
                table_name=self.name,
                dataset_name=self.dataset_id,
                project_id=self.project_id,
                rows=[
                    step_data.model_dump(),
                ],
            )
        except Exception as e:
            raise ValueError(f"Error while inserting prompt's data into BigQuery: {e}")

    def generate_new_row(self, step_data: AgentStep) -> str:
        """
        Public method to generate a new row in the agent_steps table

        Args:
            step_data: AgentStep -> Basic Info related to the step

        Returns:
            str -> step_id
        """
        # Generate step_id, already has error handlers for prompt_id
        # If the prompt exists is because the chat_session_id already existed
        step_id = self._generate_id(step_data.prompt_id)
        logger.info(f"Generated {step_id = }")

        # Store the new data into step_data
        step_data.step_id = step_id
        step_data.created_at = datetime.now(timezone.utc)

        self._insert_row(step_data)

        return step_id

    def get_chat_session_history(self, chat_session_id: str) -> list[dict]:
        """
        Generate a list of dictionaries. The list is the full chat session history

        Args:
            chat_session_id: str -> Id of the chat session

        Returns:
            list[dict] -> Full chat session history
        """
        if not self._sessions_table.session_exists(chat_session_id):
            raise ValueError("chat_session_id does not exist")

        query = f"""
            select
                step_data
            from {self.project_id}.{self.dataset_id}.{self.name}
            where chat_session_id = '{chat_session_id}'
            order by {self.primary_key} asc
        """

        rows_iterator = query_data(query)

        history = [row.step_data for row in rows_iterator]

        return history

    def store_prompt_steps(self, new_steps: list[AgentStep]) -> list[str]:
        """
        When the AI Agent generates a response it could generate multiple agent steps.
        This function handles the correct storage of them.

        Args:
            new_steps: list[AgentStep] -> List of steps generated by the prompt

        Returns:
            list[str] -> List step_ids generated
        """
        # Instanciating a list that will contain all the steps to be stored
        # in the table
        steps_to_store = list()
        # Instanciating a list that will return the step_ids
        step_ids = list()

        for step_number, step_data in enumerate(new_steps):
            if step_number == 0:
                # Get the structure of the step_id variable
                new_step_id = self._generate_id(
                    prompt_id=step_data.prompt_id,
                    chat_session_id=step_data.chat_session_id,
                )
                # Extracting the initial step number
                match = re.search(r"\d+$", new_step_id)
                initial_step_number = int(match.group(0))

            # Generating a step_id
            next_step_number = initial_step_number + step_number
            step_id = re.sub(r"\d{8}$", f"{next_step_number:08d}", new_step_id)

            # Getting the current date
            now = datetime.now(timezone.utc)

            # Replacing the values of the AgentStep objects
            step_data.step_id = step_id
            step_data.created_at = now

            # Converts step_data into a dictionary and store it into the list
            steps_to_store.append(step_data.model_dump())
            step_ids.append(step_id)

        try:
            insert_rows(
                table_name=self.name,
                dataset_name=self.dataset_id,
                project_id=self.project_id,
                rows=steps_to_store,
            )
        except Exception as e:
            raise ValueError(f"Error while inserting prompt's data into BigQuery: {e}")

        return step_ids

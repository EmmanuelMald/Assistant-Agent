from .bq_base import BigQueryTable
from assistant_agent.utils.gcp.bigquery import query_data, insert_rows
from assistant_agent.utils.auth_auxiliars import get_password_hash
from assistant_agent.config import GCPConfig
from assistant_agent.schemas import User, UserInDB
from datetime import datetime, timezone
from loguru import logger
from pydantic import SecretStr
from typing import Optional


gcp_config = GCPConfig()


class BQUsersTable(BigQueryTable):
    __name: str = gcp_config.USERS_TABLE_NAME
    __primary_key: str = gcp_config.USERS_TABLE_PK

    @property
    def name(self) -> str:
        return self.__name

    @property
    def primary_key(self) -> str:
        return self.__primary_key

    def _generate_id(self) -> str:
        """
        Generates a new user id based on the current users registered in the DB
        """
        query_last_id = f"""
                select
                    cast(regexp_extract({self.primary_key}, r"\d+$") as numeric) as last_id
                from {self.project_id}.{self.dataset_id}.{self.name}
                where created_at = (
                    select 
                        max(created_at) 
                     from {self.project_id}.{self.dataset_id}.{self.name}
                    )
                """

        # Query the BigQuery database to get the last id of the last user created
        rows_iterator = query_data(query_last_id)
        try:
            last_id = int(next(rows_iterator).last_id)
        except StopIteration:
            last_id = 0

        # Generating the user ID
        next_id = last_id + 1
        user_id = f"UID{next_id:05d}"

        return user_id

    def user_exists(self, user_id: str) -> bool:
        """
        Public method to know if a user_id exists in the
        BigQuery table.

        Args:
            user_id: str -> Id of the user

        Returns:
            bool -> True if the user exists, False otherwise
        """
        logger.info("Verifying if the user is already registered...")
        id_exists = super()._id_in_table(
            primary_key_column_name=self.primary_key,
            primary_key_row_value=user_id,
            table_name=self.name,
        )

        return id_exists

    def email_in_table(self, email: str) -> Optional[str]:
        """
        If the email exists, returns its user_id

        Args:
            email: str -> User's email

        Returns:
            Optional[str] -> If the email exists, returns its user_id
        """
        query_email = f"""
            select
                user_id
            from {self.project_id}.{self.dataset_id}.{self.name}
            where email = '{email}'
        """

        rows_iterator = query_data(query_email)

        try:
            user_id = next(rows_iterator).user_id
            return user_id

        except StopIteration:
            return None

    def get_user_data(self, user_id: str) -> Optional[UserInDB]:
        """
        Returns the user data if the user_id exists

        Args:
            user_id: str -> Id of the user

        Returns:
            Optional[UserInDB] -> UserInDB if the email is registered
        """
        query = f"""
            select
                *
            from {self.project_id}.{self.dataset_id}.{self.name}
            where {self.primary_key} = '{user_id}'
        """

        rows_iterator = query_data(query)

        try:
            # Try to get the first element (row) of the rows_iterator
            user_data = next(rows_iterator)

            userdb = UserInDB(
                user_id=user_data.user_id,
                full_name=user_data.full_name,
                email=user_data.email,
                password=SecretStr(user_data.hashed_password),
                company_name=user_data.company_name,
                company_role=user_data.company_role,
                created_at=user_data.created_at,
            )

            return userdb

        except StopIteration:  # If the iterator is empty
            return None

    def _insert_row(self, user_data: User) -> str:
        """
        Insert user data into the BigQuery database.

        Args:
            user_data: User -> User class containing the user information

        Returns:
            str -> user_id that was inserted into the BigQuery table.
        """
        logger.info("Inserting user data into BigQuery...")

        # Get the current date and time
        now = datetime.now(timezone.utc)
        current_time = now.strftime(r"%Y-%m-%d %H:%M:%S")

        logger.info("Generating a new user ID...")
        user_id = self._generate_id()
        logger.info(f"Generated user ID: {user_id}")

        logger.info("Inserting data...")

        # Hashing password
        user_data.password = get_password_hash(user_data.password)

        # Preparing the columns to fill in the BigQuery table
        data_to_insert = {
            "user_id": user_id,
            "full_name": user_data.full_name,
            "company_name": user_data.company_name,
            "email": user_data.email,
            "company_role": user_data.company_role,
            "created_at": current_time,
            "hashed_password": user_data.password.get_secret_value(),  # Hashed password
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
            raise ValueError(f"Error while inserting user's data into BigQuery: {e}")

        return user_id

    def generate_new_row(self, user_data: User) -> str:
        """
        Full process of register a new user in BigQuery, this is, check if the email already exists, if so,
        does not register a new user.

        Args:
            user_data: User -> user info

        Returns:
            user_id: str -> User id generated
        """
        if self.email_in_table(email=user_data.email):
            raise ValueError(
                "The email of the user is already registered, "
                "try with a new email or log in with it"
            )

        user_id = self._insert_row(user_data=user_data)
        logger.info("User data inserted into BigQuery")
        logger.info(f"{user_id = }")

        return user_id

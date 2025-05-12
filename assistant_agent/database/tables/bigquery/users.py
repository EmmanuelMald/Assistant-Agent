from .bq_base import BigQueryTable
from assistant_agent.utils.gcp.bigquery import query_data, insert_rows
from assistant_agent.auxiliars.auth_auxiliars import get_password_hash
from assistant_agent.config import GCPConfig
from assistant_agent.schemas import User, UserInDB
from datetime import datetime
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
        query_count_users = f"""
                select
                    count(*) as total_users
                from {self.project_id}.{self.dataset_id}.{self.name}
                """

        # Query the BigQuery database to get the total number of users
        rows = query_data(query=query_count_users)
        total_users = [row.total_users for row in rows][0]

        # Generating the user ID
        next_id = total_users + 1
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

    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Tells if an email is already registered, if so, returns all its data

        Args:
            email: str -> User's email

        Returns:
            Optional[UserInDB] -> UserInDB if the email is registered
        """
        query_email = f"""
            select
                *
            from {self.project_id}.{self.dataset_id}.{self.name}
            where email = '{email}'
        """

        rows_iterator = query_data(query_email)

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

    def get_hashed_password(self, user_id: str) -> SecretStr:
        """
        Get the hashed password of the user

        Args:
            user_id: ID of the user

        Returns:
            str -> hashed password
        """
        if not self._id_in_table(user_id=user_id):
            raise ValueError("user_id is not in table")

        query_password = f"""
            select
                hashed_password
            from {self.project_id}.{self.dataset_id}.{self.name}
            where {self.primary_key} = '{user_id}'
        """

        rows_iterator = query_data(query=query_password)

        hashed_password = SecretStr(next(rows_iterator).hashed_password)

        return hashed_password

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
        now = datetime.now()
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

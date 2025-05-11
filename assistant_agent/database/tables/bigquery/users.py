from assistant_agent.database.tables.bigquery.bq_base import BigQueryTable
from assistant_agent.utils.gcp.bigquery import query_data, insert_rows
from assistant_agent.auxiliars.auth_auxiliars import get_password_hash
from assistant_agent.config import GCPConfig
from assistant_agent.schemas import User
from datetime import datetime
from loguru import logger
from pydantic import SecretStr


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

    def _id_in_table(self, user_id: str) -> bool:
        """
        Tells if an email is already on the user's BigQuery table

        Args:
            user_id: str -> User ID

        Returns:
            bool -> True if the user already exists
        """
        logger.info("Verifying if the user is already registered...")

        query = f"""
                select
                    {self.primary_key}
                from {self.project_id}.{self.dataset_id}.{self.name}
                where {self.primary_key} = '{user_id}'
                """
        logger.debug(f"{query=}")

        rows_iterator = query_data(query)

        try:
            # Try to get the first element (row) of the rows_iterator
            next(rows_iterator)
            return True

        except StopIteration:  # If the iterator is empty
            logger.info(f"User ID '{user_id}' not found in table")
            return False

    def _email_in_table(self, email: str) -> bool:
        """
        Tells if an email is already registered

        Args:
            email: str -> User's email

        Returns:
            bool -> True of the email is already registered
        """
        query_email = f"""
            select
                user_id
            from {self.project_id}.{self.dataset_id}.{self.name}
            where email = '{email}'
        """

        query_results = query_data(query_email)

        results_list = [row[self.primary_key] for row in query_results]

        if len(results_list) > 0:
            return True

        return False

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

        query_result = query_data(query=query_password)

        hashed_password = [SecretStr(row.hashed_password) for row in query_result][0]

        return hashed_password

    def _insert_row(self, user_data: User) -> str:
        """
        Insert user data into the BigQuery database.

        Args:
            user_data: User -> User class containing the user information
            table_id (str): The name of the BigQuery table.

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
        if self._email_in_table(email=user_data.email):
            raise ValueError(
                "The email of the user is already registered,"
                "try with a new email or log in with it"
            )

        # Hash the password
        user_data.password = get_password_hash(user_data.password)

        user_id = self._insert_row(user_data=user_data)
        logger.info("User data inserted into BigQuery")
        logger.info(f"{user_id = }")

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
        return self._id_in_table(user_id=user_id)

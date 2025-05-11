from assistant_agent.database.tables import Table
from assistant_agent.config import GCPConfig
from assistant_agent.utils.gcp.bigquery import query_data

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

    def _id_in_table(
        self, primary_key_row_value: str, primary_key_column_name: str, table_name: str
    ) -> bool:
        """
        Checks if a row with a specific value in its primary_key exists or not

        Args:
            primary_key_column_name: str -> Name of the column that represents the PK
            primary_key_row_value: str -> Value of the primary key that we want to know if it exists or not
            table_name: str -> Name of the table to query

        Returns:
            bool -> True if the id exists in the table
        """
        query = f"""
            select
                {primary_key_column_name}
            from {self.project_id}.{self.dataset_id}.{table_name}
            where {primary_key_column_name} = '{primary_key_row_value}'
        """

        rows_iterator = query_data(query)

        try:
            # Try to get the first element (row) of the rows_iterator
            next(rows_iterator)
            return True

        except StopIteration:  # If the iterator is empty
            return False

from google.cloud import bigquery
from loguru import logger


client = bigquery.Client()


def dataset_exists(dataset_name: str, project_id: str) -> bool:
    """
    Check if a dataset exists in BigQuery.

    Args:
        dataset_name (str): The name of the dataset to check.
        project_id (str): The project ID where the dataset is located.

    Returns:
        bool: True if the dataset exists, False otherwise.
    """
    parameters = {"dataset_name": dataset_name, "project_id": project_id}
    if not all(
        [isinstance(param, str) and param != "" for param in parameters.values()]
    ):
        raise ValueError(
            f"The parameters {', '.join(parameters.keys())} must be not null strings."
        )

    dataset_id = f"{project_id}.{dataset_name}"

    try:
        client.get_dataset(dataset_id)
        return True
    except Exception as e:
        if "Not found" in str(e):
            return False
        else:
            raise e


def table_exists(table_name: str, dataset_name: str, project_id: str) -> bool:
    """
    Check if a table exists in a dataset in BigQuery.

    Args:
        table_name (str): The name of the table to check.
        dataset_name (str): The name of the dataset where the table is located.
        project_id (str): The project ID where the dataset is located.

    Returns:
        bool: True if the table exists, False otherwise.
    """
    parameters = {
        "table_name": table_name,
        "dataset_name": dataset_name,
        "project_id": project_id,
    }
    if not all(
        [isinstance(param, str) and param != "" for param in parameters.values()]
    ):
        raise ValueError(
            f"The parameters {', '.join(parameters.keys())} must be not null strings."
        )

    table_id = f"{project_id}.{dataset_name}.{table_name}"

    try:
        client.get_table(table_id)
        return True
    except Exception as e:
        if "Not found" in str(e):
            return False
        else:
            raise e


def create_dataset(dataset_name: str, dataset_location: str, project_id: str) -> None:
    """
    Create a new dataset in BigQuery.

    Args:
        dataset_name (str): The name of the dataset to create.
        dataset_location (str): The location of the dataset.
        project_id (str): The project ID where the dataset will be created.

    Returns:
        None
    """
    # dataset_exists already has error handlers for its parameters
    if dataset_exists(dataset_name, project_id):
        raise ValueError(
            f"Dataset {dataset_name} already exists in project {project_id}."
        )

    dataset_id = f"{project_id}.{dataset_name}"

    dataset = bigquery.Dataset(dataset_id)
    dataset.location = dataset_location

    try:
        client.create_dataset(dataset)
        logger.info(f"Dataset {dataset_name} created.")
    except Exception as e:
        logger.info(f"Error creating the dataset: {e}")


def create_table(
    table_name: str, dataset_name: str, project_id: str, schema: dict
) -> None:
    """
    Create a new table in a dataset in BigQuery.

    Args:
        table_name (str): The name of the table to create.
        dataset_name (str): The name of the dataset where the table will be created.
        project_id (str): The project ID where the dataset is located.
        schema (dict): The schema of the table to create.

                The keys are the column names and the values are the data types. Ex:
                {
                    "column_name": "STRING",
                    "column_name2": "INTEGER",
                    "column_name3": "FLOAT",
                    "column_name4": "TIMESTAMP"
                }
                To see all the data types, see:
                https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types

    Returns:
        None
    """
    # table_exists already has error handlers for its parameters
    if table_exists(table_name, dataset_name, project_id):
        raise ValueError(
            f"Table {table_name} already exists in dataset {dataset_name}."
        )

    table_id = f"{project_id}.{dataset_name}.{table_name}"

    schema = [
        bigquery.SchemaField(column_name, datatype)
        for column_name, datatype in schema.items()
    ]

    table = bigquery.Table(table_id, schema=schema)

    try:
        client.create_table(table)
        logger.info(f"Table {table_name} created.")
    except Exception as e:
        logger.info(f"Error creating the table: {e}")


def delete_dataset(dataset_name: str, project_id: str) -> None:
    """
    Delete a dataset in BigQuery.

    Args:
        dataset_name (str): The name of the dataset to delete.
        project_id (str): The project ID where the dataset is located.

    Returns:
        None
    """
    # dataset_exists already has error handlers for its parameters
    if not dataset_exists(dataset_name, project_id):
        raise ValueError(
            f"Dataset {dataset_name} does not exist in project {project_id}."
        )

    dataset_id = f"{project_id}.{dataset_name}"

    try:
        client.delete_dataset(dataset_id, delete_contents=True)
        logger.info(f"Dataset {dataset_name} deleted.")
    except Exception as e:
        raise ValueError(f"Error deleting the dataset: {e}")


def delete_table(table_name: str, dataset_name: str, project_id: str) -> None:
    """
    Delete a table in a dataset in BigQuery.

    Args:
        table_name (str): The name of the table to delete.
        dataset_name (str): The name of the dataset where the table is located.
        project_id (str): The project ID where the dataset is located.

    Returns:
        None
    """
    # table_exists already has error handlers for its parameters
    if not table_exists(table_name, dataset_name, project_id):
        raise ValueError(
            f"Table {table_name} does not exist in dataset {dataset_name}."
        )

    table_id = f"{project_id}.{dataset_name}.{table_name}"

    try:
        client.delete_table(table_id)
        logger.info(f"Table {table_name} deleted.")
    except Exception as e:
        raise ValueError(f"Error deleting the table: {e}")


def query_data(query: str) -> list:
    """
    Query data from a table in BigQuery.

    Args:
        query (str): The SQL query to execute.

    Returns:
        list: A list of rows returned by the query.
    """
    if not isinstance(query, str) or query == "":
        raise ValueError("The query must be a non-empty string.")

    try:
        query_job = client.query(query)
        results = query_job.result()
        return results

    except Exception as e:
        raise ValueError(f"Error querying the data: {e}")


def insert_rows(
    table_name: str, dataset_name: str, project_id: str, rows: list[dict]
) -> None:
    """
    Insert rows into a table in BigQuery.

    Args:
        table_name (str): The name of the table to insert rows into.
        dataset_name (str): The name of the dataset where the table is located.
        project_id (str): The project ID where the dataset is located.
        rows (list): A list of dictionaries representing the rows to insert. Ex:

                    [
                        {
                            "column_name": "value",
                            "column_name2": 123,
                            "column_name3": 123.45,
                            "column_name4": "2023-10-01T00:00:00Z"
                        },
                        {
                            "column_name": "value2",
                            "column_name2": 456,
                            "column_name3": 678.90,
                            "column_name4": "2023-10-02T00:00:00Z"
                        }
                    ]

    Returns:
        None
    """
    # table_exists already has error handlers for its parameters
    if not table_exists(table_name, dataset_name, project_id):
        raise ValueError(
            f"Table {table_name} does not exist in dataset {dataset_name}."
        )

    table_id = f"{project_id}.{dataset_name}.{table_name}"

    try:
        errors = client.insert_rows_json(table_id, rows)
        if errors:
            raise ValueError(f"Errors occurred while inserting rows: {errors}")
        logger.info(f"Rows inserted into {table_name}.")
    except Exception as e:
        raise ValueError(f"Error inserting rows: {e}")


def update_row(
    table_name: str,
    dataset_name: str,
    project_id: str,
    primary_key_column_name: str,
    row_id: str,
    update_data: dict,
) -> None:
    """
    Update a row in a table in BigQuery.

    Args:
        table_name (str): The name of the table to update the row in.
        dataset_name (str): The name of the dataset where the table is located.
        project_id (str): The project ID where the dataset is located.
        primary_key_column_name (str): The name of the primary key column in the table.
        row_id (str): The ID of the row to update.
        update_data (dict): A dictionary representing the data to update. Ex:

                    {
                        "column_name": "new_value",
                        "column_name2": 123,
                        "column_name3": 123.45,
                        "column_name4": "2023-10-01T00:00:00Z"
                    }

    Returns:
        None
    """
    # table_exists already has error handlers for its parameters
    if not table_exists(table_name, dataset_name, project_id):
        raise ValueError(
            f"Table {table_name} does not exist in dataset {dataset_name}."
        )

    table_id = f"{project_id}.{dataset_name}.{table_name}"

    try:
        query = f"""
            UPDATE `{table_id}`
            SET {", ".join([f"{key} = '{value}'" for key, value in update_data.items()])}
            WHERE {primary_key_column_name} = '{row_id}'
        """
        client.query(query).result()
        logger.info(f"Row with ID {row_id} updated in {table_name}.")
    except Exception as e:
        raise ValueError(f"Error updating row: {e}")

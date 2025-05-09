import sys

sys.path.append("..")

from assistant_agent.auxiliars.db_auxiliars import user_in_db, insert_user_data
from assistant_agent.auxiliars.auth_auxiliars import get_password_hash
from assistant_agent.schemas import User


def register_new_user(user_data: User) -> str:
    """
    Register a new user in the DataBase

    Args:
        user_data: User -> Data related to the new user

    Returns:
        str -> user_id generated
    """
    user_db = user_in_db(email=user_data.email)

    # If the email is already in the DB
    if user_db.hashed_password:
        raise ValueError("The email is already registered")

    # Generate hashed password
    hashed_password = get_password_hash(password=user_data.password)
    user_data.password = hashed_password

    user_id = insert_user_data(user_data=user_data)

    return user_id

from passlib.context import CryptContext
from pydantic import SecretStr


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: SecretStr, hashed_password: SecretStr) -> bool:
    return pwd_context.verify(
        plain_password.get_secret_value(), hashed_password.get_secret_value()
    )


def get_password_hash(password: SecretStr) -> SecretStr:
    return SecretStr(pwd_context.hash(password.get_secret_value()))

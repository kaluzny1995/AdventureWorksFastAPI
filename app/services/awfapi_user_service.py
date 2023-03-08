from passlib.context import CryptContext

from app.providers import AWFAPIUserProvider


class AWFAPIUserService:
    pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
    awfapi_user_provider: AWFAPIUserProvider = AWFAPIUserProvider()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

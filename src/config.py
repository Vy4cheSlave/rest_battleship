from pydantic_settings import BaseSettings

class DBSettings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra='ignore'
        

    def database_url_asyncpg(self) -> str:
        # postgresql+asyncpg://user:password@host:port/name
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

db_settings = DBSettings()

class JWTSettings(BaseSettings):
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int
    jwt_refresh_token_expire_days: int

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra='ignore'

jwt_settings = JWTSettings()
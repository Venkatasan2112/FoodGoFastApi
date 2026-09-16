from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    database_hostname: str
    database_port: int
    database_password: str
    database_name: str
    database_username: str
    redis_url: str
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    FTP_HOST: str
    FTP_USER: str
    FTP_PASSWORD: str
    FTP_BASEPATH: str
    FTP_EVENT_FILENAME: str
    MINIO_HOST: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env_smidt",
        env_file_encoding="utf-8",
    )


settings = Settings()

from pydantic_settings import BaseSettings

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    DEBUG= os.environ.get('DEBUG')

class Settings_SQLITE(BaseSettings):
    DB_URL: str = "sqlite:///./test.db"
    DB_ECHO: bool = False
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60*24
    
class Settings(BaseSettings):
    DB_URL: str = os.environ.get('DB_URL')
    DB_ECHO: bool = False
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60*24
    DB_URL_PASS_OLD: str = os.environ.get('DB_URL_PASS_OLD')
    DB_URL_HOST_OLD: str = os.environ.get('DB_URL_HOST_OLD')
    DB_URL_PORT_OLD: int = int(os.environ.get('DB_URL_PORT_OLD'))
    DB_URL_USER_OLD: str = os.environ.get('DB_URL_USER_OLD')
    DB_URL_DB_OLD: str = os.environ.get('DB_URL_DB_OLD')
    EMAIL_CARDUMEN_USER: str = os.environ.get('EMAIL_CARDUMEN_USER')
    EMAIL_CARDUMEN_SERVER: str = os.environ.get('EMAIL_CARDUMEN_SERVER')
    EMAIL_CARDUMEN_SECRET: str = os.environ.get('EMAIL_CARDUMEN_SECRET')
    SYNOLOGY_FOLDER_NOTES: str = os.environ.get('SYNOLOGY_FOLDER_NOTES')
    SYNOLOGY_SERVER: str = os.environ.get('SYNOLOGY_SERVER')
    SYNOLOGY_PORT: str = os.environ.get('SYNOLOGY_PORT')
    EMAIL_ADDRESS: str = os.environ.get('EMAIL_ADDRESS')
    EMAIL_SECRET: str = os.environ.get('EMAIL_SECRET')
    SECRET_KEY: str = os.environ.get('SECRET_KEY')
    REDIS_URL: str = os.environ.get('REDIS_URL')

settings = Settings()

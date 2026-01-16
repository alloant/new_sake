from pydantic_settings import BaseSettings

import os

basedir = os.path.abspath(os.path.dirname(__file__))

LAYOUT = 'columns'

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
    DB_URL_OLD_PASS: str = os.environ.get('DB_URL_OLD_PASS')

settings = Settings()

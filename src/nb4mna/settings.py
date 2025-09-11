from pydantic_settings import BaseSettings

from .modules.fight.settings import TatsumakiSettings


class Settings(BaseSettings):
    tatsumaki: TatsumakiSettings

    class Config:
        env_file = '.env'
        env_nested_delimiter = '__'


settings = Settings()

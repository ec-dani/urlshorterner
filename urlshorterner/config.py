from pydantic import BaseSettings
from functools import lru_cache

@lru_cache()
def get_settings():
    return Settings()

class Settings(BaseSettings):
  class Config:
     env_file = ".env"

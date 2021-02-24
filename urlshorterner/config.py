from dotenv import load_dotenv
from functools import lru_cache
import os

@lru_cache()
def cached_dotenv():
  load_dotenv()

cached_dotenv()
MONGO_URI= os.environ.get("MONGO_URI")
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = float(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"))

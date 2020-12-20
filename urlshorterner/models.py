from pydantic import BaseModel
from typing import Optional

class Link(BaseModel):
  url: str
  url_shorter: Optional[str] = None


class User(BaseModel):
    username: str
    hashed_password: str
    full_name: Optional[str] = None
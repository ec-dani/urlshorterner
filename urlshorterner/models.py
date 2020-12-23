from pydantic import BaseModel
from typing import Optional
from urlshorterner.types import PyObjectId
from bson import ObjectId
class Link(BaseModel):
  _id: PyObjectId
  url: str
  url_shorter: Optional[str] = None
  class Config:
    arbitrary_types_allow = True
    json_encoders = {ObjectId: str}


class User(BaseModel):
  _id: PyObjectId
  username: str
  full_name: Optional[str] = None
  class Config:
    arbitrary_types_allow = True
    json_encoders = {ObjectId: str}

class UserInDB(User):
    hashed_password: str
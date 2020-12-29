from pydantic import BaseModel
from typing import Optional,List
from urlshorterner.types import PyObjectId
from bson import ObjectId
class Link(BaseModel):
  url: str
  url_shorter: Optional[str] = None

class User(BaseModel):
  _id: PyObjectId
  username: str
  full_name: Optional[str] = None
  links: List[Link] = []
  class Config:
    arbitrary_types_allow = True
    json_encoders = {ObjectId: str}

class UserInDB(User):
    password: str

class Token(BaseModel):
  access_token: str
  token_type: str

class TokenData(BaseModel):
  username: Optional[str] = None
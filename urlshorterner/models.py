from pydantic import BaseModel, validator
from typing import Optional,List
from urlshorterner.types import PyObjectId
from bson import ObjectId
from urlshorterner.utils import get_password_hash
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
  def hash_password(self):
    self.password= get_password_hash(self.password)

class Token(BaseModel):
  access_token: str
  token_type: str

class TokenData(BaseModel):
  username: Optional[str] = None
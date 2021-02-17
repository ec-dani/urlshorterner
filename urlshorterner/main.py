from fastapi import FastAPI,Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.responses import RedirectResponse
from urlshorterner.models import User,Link,UserInDB, Token, TokenData
from pymongo import MongoClient
from bson import json_util
from urlshorterner.utils import get_password_hash,verify_password,create_access_token
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import urlshorterner.settings as SETTINGS
import random
import string
import validators

app = FastAPI()
client = MongoClient(SETTINGS.MONGO_URI)
db= client['urlshorterner']
users_col= db['users']
links_col = db['links']
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def authenticate_user(username, password):
  vuser = users_col.find_one({"username": username})
  if not vuser:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="usuario incorrecto")
  user = UserInDB(**vuser)
  if not verify_password(password, user.password):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña incorrecta")
  return user

def get_user(token: str = Depends(oauth2_scheme)):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(token, SETTINGS.SECRET_KEY, algorithms=[SETTINGS.ALGORITHM])
    username: str = payload.get("sub")
    if username is None:
      raise credentials_exception
    token_data = TokenData(username= username)
  except JWTError:
    raise credentials_exception
  user= users_col.find_one({"username":token_data.username})
  return User(**user)

def random_string():
  letter = string.ascii_lowercase
  resul="ec_"
  for i in range(5):
	  resul += random.choice(letter)
  return resul

@app.get("/")
async def root():
  return{"message": f"API urlshorter by me" }

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
  user= authenticate_user(form_data.username, form_data.password )
  if not user:
    raise HTTPException(
      status_code= status.HTTP_401_UNAUTHORIZED,
      detail= "Incorrect username or password",
      headers={"WWW-Authenticate": "Bearer"}
    )
  access_token_expires= timedelta(minutes= SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(data= {"sub": user.username}, expires_delta= access_token_expires)
  return {"access_token": access_token, "token_type": "bearer"}

@app.post("/user")
async def add_a_user(user: UserInDB):
  new_user= users_col.find_one({"username": user.username})
  if new_user is not None:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este usuario ya existe")
  user.hash_password()
  users_col.insert_one(
    user.dict()
  )
  return {"message": f"Usuario guardado {user.username}"}


@app.get("/user/me", response_model= User)
async def show_user_data(current_user: User= Depends(get_user)):
  return current_user

@app.get("/user")
async def show_all_users():
  users = []
  for user in users_col.find():
    users.append(User(**user))
  if not users:
    return {"message": "mas solo que la una"}
  return users

@app.post("/user/url", response_model= Link)
async def add_a_private_url(link: Link, current_user:User =Depends(get_user)):
  if not validators.url(link.url):
    raise HTTPException(status_code= status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Formato incorrecto")
  if link.url in [dlink.url for dlink in current_user.links]:
    raise HTTPException(status_code= status.HTTP_409_CONFLICT, detail="URL ya existe")
  link.url_shorter = link.url_shorter or random_string()
  current_user.links.append(link)
  new_links =[link.dict() for link in current_user.links]
  users_col.update_one({"username": current_user.username},{"$set":{"links": new_links}} )
  return link

@app.get("/user/url")
async def show_your_urls(current_user: User= Depends(get_user)):
  if not current_user.links:
    return {"message": "aun no tienes ninguna url"}
  return current_user.links

@app.get("/users/url/{furl_shorter}")
async def go_to_private(furl_shorter:str, current_user:User = Depends(get_user)):
  short_url = None
  for link in current_user.links:
    if link.url_shorter == furl_shorter:
      short_url=link.url
  if short_url is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
  return RedirectResponse(url=short_url)

@app.post("/link")
async def add_public_link(link: Link):
  if not validators.url(link.url):
    raise HTTPException(status_code= status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Formato incorrecto")
  new_url= links_col.find_one({"url":link.url})
  if new_url is not None:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="URL ya guardada")
  link.url_shorter = link.url_shorter or random_string()
  links_col.insert_one({
    "url": link.url,
    "url_shorter": link.url_shorter
  })
  return link

@app.get("/links")
async def show_public_links():
  links= []
  for link in links_col.find():
    links.append(Link(**link))
  if not links:
    return{"message":"no hay links"}
  return links

@app.get("/url/{furl_shorter}")
async def go_to(furl_shorter: str):
  short = links_col.find_one({"url_shorter": furl_shorter })
  if short is None:
    raise HTTPException(status_code= status.HTTP_404_NOT_FOUND)
  return RedirectResponse(url=short["url"] )
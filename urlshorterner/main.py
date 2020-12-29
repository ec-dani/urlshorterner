from fastapi import FastAPI,Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.responses import RedirectResponse
from urlshorterner.models import User,Link,UserInDB, Token, TokenData
from pymongo import MongoClient
from bson import json_util
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import json
import redis
import random
import string

SECRET_KEY= "cafec8b9b325fa68ad398c5c35c11ec66c43aca33b9fd5e3ddf6321cf6cfc8e3"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()
#r = redis.Redis()
client = MongoClient('mongodb://localhost:27017/')
db= client['urlshorterner']
users_col= db['users']
links_col = db['links']
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
  return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
  return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username, password):
  vuser = users_col.find_one({"username": username})
  user = UserInDB(**vuser)
  if not user:
    return {"message":"usuario NO encontrado"}
  if not verify_password(password, user.password):
    return{"message": "contraseña Incorrecta"}
  return user

def create_access_token (data: dict, expires_delta: Optional[timedelta]= None):
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.utcnow() + expires_delta
  else:
    expire = datetime.utcnow() + timedelta(minutes=15)
  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  return encoded_jwt

def get_user(token: str = Depends(oauth2_scheme)):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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

#MAL IMPLEMENTADO
@app.post("/url")
async def add_a_private_url(link: Link, current_user:User =Depends(get_user)):
  new_link=link
  user_link_list = current_user.links
  if new_link.url in user_link_list:
    return{"message": "ya existe esta url"}
  new_link.url_shorter = new_link.url_shorter or random_string()
  user_link_list.append(new_link)
  users_col.update({"username": current_user.username}, {"links": user_link_list})
  return {"message": "Guardado"}
    

@app.get("/urls")
async def show_your_urls(current_user: User= Depends(get_user)):
  if not current_user.links:
    return {"message": "aun no tienes ningun url"}
  return current_user.links


#Usar UserInDB
@app.post("/user")
async def add_a_user(user: UserInDB):
  new_user= users_col.find_one({"username": user.username})
  if new_user is not None:
    return {"message":"Este usuario ya existe"}
  users_col.insert_one({
    'username': user.username,
    'password': get_password_hash(user.password),
    'full_name':  user.full_name,
    'links': user.links
  })
  return {"message": f"Usuario guardado {user.username}"}

@app.get("/users")
async def show_all_users():
  users = []
  for user in users_col.find():
    users.append(User(**user))
  if not users:
    return {"message": "mas solo que la una"}
  return users
 # users = list(users_col.find())
 # return json.loads(json_util.dumps(users))


@app.get("/url/{furl_shorter}")
async def go_to(furl_shorter: str):
  short = links_col.find_one({"url_shorter": furl_shorter })
  if short is None:
    return {"message":"no encontrado"}
  return RedirectResponse(url=short["url"] )

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
  user= authenticate_user(form_data.username, form_data.password )
  if not user:
    raise HTTPException(
      status_code= status.HTTP_401_UNAUTHORIZED,
      detail= "Incorrect username or password",
      headers={"WWW-Authenticate": "Bearer"}
    )
  access_token_expires= timedelta(minutes= ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(data= {"sub": user.username}, expires_delta= access_token_expires)
  return {"access_token": access_token, "token_type": "bearer"}

@app.get("/user", response_model= User)
async def show_user_data(current_user: User= Depends(get_user)):
  return current_user

@app.get("/links")
async def get_user_links(current_user: User=Depends(get_user)):
  return current_user.links
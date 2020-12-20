from fastapi import FastAPI,Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.responses import RedirectResponse
from urlshorterner.models import User,Link
from pymongo import MongoClient
from bson import json_util
import json
import redis
import random
import string

app = FastAPI()
#r = redis.Redis()
client = MongoClient('mongodb://localhost:27017/')
db= client['urlshorterner']
users_col= db['users']
links_col = db['links']
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserInDB(User):
    hashed_password: str

def fake_hash_password(password: str):
    return "ec_" + password

def random_string():
  letter = string.ascii_lowercase
  resul="ec_"
  for i in range(5):
	  resul += random.choice(letter)
  return resul


@app.get("/")
async def root():
  return{"message": f"API urlshorter by me" }

@app.post("/url/")
async def add_a_url(link: Link):
  new_link = links_col.find_one({"url": link.url})
  if new_link is None:
    url_shorter = link.url_shorter or random_string()
    links_col.insert_one({
      "url": link.url,
      "url_shorter": url_shorter
    })
    return  {"message": f" {link.url} guardado como {url_shorter}"}
  return {"message": "este link ya está guardado"}

@app.get("/urls")
async def show_all_urls():
  urls =json.loads(json_util.dumps(list(links_col.find())))
  if not urls:
    return {"message": "mas solo que la una"}
  return urls

@app.post("/user")
async def add_a_user(user: User):
  users_col.insert_one({
    'username': user.username,
    'hashed_password': user.hashed_password,
    'full_name':  user.full_name
  })
  return {"message": f"Usuario guardado {user.username}"}

@app.get("/users")
async def show_all_users():
  users = list(users_col.find())
  return json.loads(json_util.dumps(users))


@app.get("/url/{furl_shorter}")
async def go_to(furl_shorter: str):
  short = links_col.find_one({"url_shorter": furl_shorter })
  jshort = json.loads(json_util.dumps(short))
  if short is None:
    return {"message":"no encontrado"}
  return RedirectResponse(url=jshort["url"] )

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
  user_dict = users_col.find_one({"username": form_data.username})
  if not user_dict:
    raise HTTPException(status_code=400, detail="Usuario incorrecto ")
  user = UserInDB(**user_dict)
  hashed_password = form_data.password
  if not hashed_password == user.hashed_password:
    raise HTTPException(status_code=400, detail="Contraseña incorrecta")
  return {"access_token": user.username, "token_type": "bearer"}

@app.get("/secreto")
async def show_secret_message(token:str = Depends(oauth2_scheme)):
  return "tomatela puto"


# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
from fastapi import FastAPI
from starlette.responses import RedirectResponse
from pydantic import BaseModel
import redis
import random
import string

class Item(BaseModel):
  url: str
  url_shorter: str= None

app = FastAPI()
r = redis.Redis()

def random_string():
  letter = string.ascii_lowercase
  resul="ec_"
  for i in range(5):
	  resul += random.choice(letter)
  return resul


@app.get("/")
async def root():
  return{"message": "API urlshorter by me" }

@app.get("/urls")
async def show_all_urls():
  arr = []
  for url in r.keys():
    arr.append({url.decode("utf8"): r.get(url).decode("utf8")})
  if not arr :
    return {"message": "mas solo que la uno bro"}
  return arr

@app.post("/item/")
async def add_a_url(item: Item):
  if r.get(item.url) is None:
    url_shorter = item.url_shorter or random_string()
    r.set(item.url,url_shorter)
    return{"message": f"se ha guardado {item.url} con {url_shorter}"}
  return{"messsage": f"{item.url} ya esta guardada"}

@app.get("/url/{url_shorter}")
async def go_to(url_shorter: str):
  for url in r.keys():
    if r.get(url).decode("utf8") == url_shorter:
      return RedirectResponse(url= url.decode("utf8"))
  return {"message":"no se ha encontrado"}



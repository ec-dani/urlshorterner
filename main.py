from fastapi import FastAPI
from starlette.responses import RedirectResponse


app = FastAPI()

urls = [
  {
  "url":"https://www.google.com/",
  "url_shorter": "buscaguay"
  },
  {
    "url":"https://www.youtube.com/",
    "url_shorter":"videoguay"
  }
]

@app.get("/")
async def root():
  return{"message": "Holaaa puutoos"}

@app.get("/urls")
async def show_all_urls():
  return urls

@app.post("/url/")
async def add_a_url(url: str , url_shorter:str):
  if not url and url_shorter:
    return {"message":"url esta vacia y/o url_shorter tambien"}
  urls.append({"url":url, "url_shorter": url_shorter})
  return {"message": f"{url} añadida con {url_shorter} como url_shorter"}

@app.get("/url/{url_shorter}")
async def go_to(url_shorter: str):
  for url in urls:
    if url["url_shorter"] == url_shorter:
      return RedirectResponse(url= url["url"])
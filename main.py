from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.wsgi import WSGIMiddleware
from housing import app as housing
# from location_map import app as location_map


app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
app.mount("/housing", WSGIMiddleware(housing.server))
# app.mount("/location_map", WSGIMiddleware(location_map.server))
templates = Jinja2Templates(directory='templates')


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(
        "house_dash.html", {"request": request})


# @app.get("/")
# def index():
#     return "Go ~/housing or ~/location_map [ WIP ] to see our property apps"


# @app.get("/public_housing", response_class=HTMLResponse)
# async def read_root(request: Request):
#     return templates.TemplateResponse("house_dash.html",
#                                       {"request": request})

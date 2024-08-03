from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from public_housing import app as public_housing
from location_map import app as location_map

app = FastAPI()
app.mount("/public_housing", WSGIMiddleware(public_housing.server))
app.mount("/location_map", WSGIMiddleware(location_map.server))


@app.get("/")
def index():
    return "Go ~/public_housing or ~/location_map to see your apps"

import jinja2
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from public_housing import app as public_housing
from fastapi_blog import add_blog_to_fastapi
import public_dash as pud
# from private_housing import app as private_housing
# from location_map import app as location_map

django_style_jinja2_loader = jinja2.ChoiceLoader([
    jinja2.FileSystemLoader("templates"),
    jinja2.PackageLoader("fastapi_blog", "templates"),
])

app = FastAPI()
app = add_blog_to_fastapi(app, jinja2_loader=django_style_jinja2_loader)

app.mount('/static', StaticFiles(directory='static'), name='static')
app.mount("/public_housing", WSGIMiddleware(public_housing.server))
# app.mount("/private_housing", WSGIMiddleware(private_housing.server))
# app.mount("/location_map", WSGIMiddleware(location_map.server))
templates = Jinja2Templates(directory='templates')


@app.get("/public-homes")
async def read_root(request: Request):
    return templates.TemplateResponse(
        "public_home_dash.html", {"request": request})


# @app.get("/private-homes")
# async def private_housing(request: Request):
#     return templates.TemplateResponse(
#         "private_home_dash.html", {"request": request})

@app.get("/sg-public-home-trends", response_class=HTMLResponse)
async def sg_public_dash(request: Request):

    price_dist = pud.create_home_price_dist()
    mil_bar_chart = pud.create_mil_bar_chart()
    price_grp_counts = pud.create_price_grp_counts()
    price_grp_percent = pud.create_price_grp_percent()

    return templates.TemplateResponse(
        "dash_v2.html", {
            "request": request,
            "price_dist": price_dist,
            "mil_bar_chart": mil_bar_chart,
            "price_grp_counts": price_grp_counts,
            "price_grp_percent": price_grp_percent,
        })


@app.get("/")
async def root():
    return RedirectResponse(url="/sg-public-home-trends")


# Have separate endpoint for geospatial work
# @app.get("/public_housing", response_class=HTMLResponse)
# async def read_root(request: Request):
#     return templates.TemplateResponse("house_dash.html",
#                                       {"request": request})

# Start the FastAPI server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")

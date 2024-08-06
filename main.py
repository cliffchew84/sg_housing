import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.wsgi import WSGIMiddleware
from housing import app as housing
from fastapi_blog import add_blog_to_fastapi
# from location_map import app as location_map


app = FastAPI()
app = add_blog_to_fastapi(app)
app.mount('/static', StaticFiles(directory='static'), name='static')
app.mount("/housing", WSGIMiddleware(housing.server))
# app.mount("/location_map", WSGIMiddleware(location_map.server))
templates = Jinja2Templates(directory='templates')


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(
        "house_dash.html", {"request": request})

gurl = "https://raw.githubusercontent.com/cliffchew84/cliffchew84.github.io/"
bar_plot = "master/profile/assets/charts/mth_barline_chart.html"
box_plot = "master/profile/assets/charts/mth_boxplot.html"
stackbar_values = "master/profile/assets/charts/mth_stack_bar_values.html"
stackbar_percent = "master/profile/assets/charts/mth_stack_bar_percent.html"


@app.get("/sg-public-home-trends", response_class=HTMLResponse)
async def render_html(request: Request):
    try:
        resp_1 = requests.get(gurl + box_plot)
        resp_1.raise_for_status()  # Check for HTTP errors
        html_content_1 = resp_1.text

        resp_2 = requests.get(gurl + bar_plot)
        resp_2.raise_for_status()  # Check for HTTP errors
        html_content_2 = resp_2.text

        resp_3 = requests.get(gurl + stackbar_values)
        resp_3.raise_for_status()  # Check for HTTP errors
        html_content_3 = resp_3.text

        resp_4 = requests.get(gurl + stackbar_percent)
        resp_4.raise_for_status()  # Check for HTTP errors
        html_content_4 = resp_4.text

        return templates.TemplateResponse(
            "dash_page.html", {
                "request": request,
                "gh_html_content_1": html_content_1,
                "gh_html_content_2": html_content_2,
                "gh_html_content_3": html_content_3,
                "gh_html_content_4": html_content_4,
            })
    except requests.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching HTML: {str(e)}")

# @app.get("/")
# def index():
#     return "Go ~/housing or ~/location_map [ WIP ] to see our property apps"

# Have this separate endpoint once I have more content to share
# @app.get("/public_housing", response_class=HTMLResponse)
# async def read_root(request: Request):
#     return templates.TemplateResponse("house_dash.html",
#                                       {"request": request})

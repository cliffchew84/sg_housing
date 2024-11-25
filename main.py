import requests
import jinja2
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi_blog import add_blog_to_fastapi
# from public_housing import app as public_housing
from private_housing import app as private_housing
import public_dash as pud 
# from location_map import app as location_map

django_style_jinja2_loader = jinja2.ChoiceLoader([
    jinja2.FileSystemLoader("templates"),
    jinja2.PackageLoader("fastapi_blog", "templates"),
])

app = FastAPI()
app = add_blog_to_fastapi(app, jinja2_loader=django_style_jinja2_loader)

app.mount('/static', StaticFiles(directory='static'), name='static')
app.mount("/public_housing", WSGIMiddleware(public_housing.server))
app.mount("/private_housing", WSGIMiddleware(private_housing.server))
# app.mount("/location_map", WSGIMiddleware(location_map.server))
templates = Jinja2Templates(directory='templates')


@app.get("/public-homes")
async def read_root(request: Request):
    return templates.TemplateResponse(
        "public_home_dash.html", {"request": request})


@app.get("/private-homes")
async def private_housing(request: Request):
    return templates.TemplateResponse(
        "private_home_dash.html", {"request": request})


gurl = "https://raw.githubusercontent.com/cliffchew84/cliffchew84.github.io/"
bar_plot = "master/profile/assets/charts/mth_barline_chart.html"
box_plot = "master/profile/assets/charts/mth_boxplot.html"
stackbar_values = "master/profile/assets/charts/mth_stack_bar_values.html"
stackbar_percent = "master/profile/assets/charts/mth_stack_bar_percent.html"

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



# @app.get("/sg-public-home-trends", response_class=HTMLResponse)
# async def render_html(request: Request):
#     try:
#         resp_1 = requests.get(gurl + box_plot)
#         resp_1.raise_for_status()  # Check for HTTP errors
#         html_content_1 = resp_1.text
#
#         resp_2 = requests.get(gurl + bar_plot)
#         resp_2.raise_for_status()  # Check for HTTP errors
#         html_content_2 = resp_2.text
#
#         resp_3 = requests.get(gurl + stackbar_values)
#         resp_3.raise_for_status()  # Check for HTTP errors
#         html_content_3 = resp_3.text
#
#         resp_4 = requests.get(gurl + stackbar_percent)
#         resp_4.raise_for_status()  # Check for HTTP errors
#         html_content_4 = resp_4.text
#
#         return templates.TemplateResponse(
#             "dash_page.html", {
#                 "request": request,
#                 "gh_html_content_1": html_content_1,
#                 "gh_html_content_2": html_content_2,
#                 "gh_html_content_3": html_content_3,
#                 "gh_html_content_4": html_content_4,
#             })
#     except requests.RequestException as e:
#         raise HTTPException(
#             status_code=500, detail=f"Error fetching HTML: {str(e)}")
#

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

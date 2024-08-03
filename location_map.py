from pymongo import mongo_client
from dash import Dash, html, Input, Output, dcc, State
from dotenv import load_dotenv
from utils import onemap_fun as om
from utils import html_fun as hf

import os
import pandas as pd
import dash_leaflet as dl
import dash_bootstrap_components as dbc

# Simple parameter to trigger mongoDB instead of using local storage
load_dotenv()
mongo = os.getenv('mongo_')
if mongo:
    MONGO_PASSWORD = os.environ["mongo_pw"]
    base_url = "mongodb+srv://cliffchew84:"
    end_url = "cliff-nlb.t0whddv.mongodb.net/?retryWrites=true&w=majority"
    mongo_url = f"{base_url}{MONGO_PASSWORD}@{end_url}"

    db = mongo_client.MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    db_nlb = db["nlb"]

    query_output = db_nlb['p_attractions'].find({}, {})
    documents_list = list(query_output)
    att_df = pd.DataFrame(documents_list)

    query_output = db_nlb['p_mrt'].find({}, {})
    documents_list = list(query_output)
    mrt_df = pd.DataFrame(documents_list)

else:
    # These are all the amenities locations with lat-longs
    mrt_df = pd.read_csv("data/p_mrt.csv")
    att_df = pd.read_csv("data/p_attractions.csv")


c = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css"
app = Dash(__name__,
           external_stylesheets=[c, dbc.themes.BOOTSTRAP],
           requests_pathname_prefix="/location_map/")


# Icons
hse_icon = dict(html=hf.icon_html('house', color='black', bg='white'))
train_icon = dict(html=hf.icon_html('train-subway', color='white', bg='black'))
att_icon = dict(html=hf.icon_html('masks-theater', color='white', bg='black'))

# Actual Map Layout
app.layout = html.Div([
    html.H1(
        children="PoC - Singapre Location Accessibility Tool",
        style={"textAlign": "left", "padding": "5px", "color": "#555"},
    ),
    html.P(
        """This proof-of-concept uses Dash, FastAPI and Leaflet to create a
        geospatial web app that shows results taken from OneMap API, and
        geospatial API services created by the Singapore Land Authority (SLA).
        This web app allows you to search for a location in Singapore, and
        find its nearest MRTs, based on walking distance.""",
        style={"textAlign": "center", "color": "#555"},
    ),
    html.Hr(
        style={
            "borderWidth": "3px",
            "width": "100%",
            "color": "#007BFF",
            "margin": "auto",
        }
    ),
    html.Div(
        children=[
            html.Label("Location", style={"padding": '10px'}),
            dcc.Input(
                type='text',
                id="input-on-submit",
                debounce=True,
                placeholder="Search for location",
                style={'width': '30%'}),
            html.Label("Boundary", style={"padding": '10px'}),
            dcc.Dropdown(options=[1000, 1500, 2000],
                         value=1000, id="boundary"),
            html.Button('Button', id='submit-val'),
            # html.Button('Re-center Map', id='recenter-map',
            #             style={"margin-left": "10px"})
        ],
        style={"display": "flex", "width": "70%", "padding": "10px"},
    ),
    html.Div(id="submit-val-output"),
    html.Div(children=[
        dcc.Loading(children=[
            html.Div(children=[
                dl.Map([dl.LayersControl(dl.TileLayer())],
                       center=(1.310270, 103.821959), zoom=11, id='map',
                       style={'height': '70vh', 'width': '80vh'}),
                html.Div(id="table-output", style={'padding': '10px',
                                                   'flex': '1'}),
            ], style={'display': 'flex', 'width': '100%'})
        ])
    ])
])


@app.callback(
    [Output('map', 'children'), Output('table-output', 'children')],
    Input('submit-val', 'n_clicks'),
    [State("boundary", "value"), State('input-on-submit', 'value')],
    prevent_initial_call=True)
def update_map(n_clicks, boundary, value):
    # Make OneMap API call
    zoom_val = 15 if boundary <= 1500 else 14
    final_msg = None

    kw_json = om.loc_best_match(value)
    kw_latlon = (kw_json.get("LATITUDE"), kw_json.get("LONGITUDE"))
    kw_add = kw_json.get('ADDRESS')

    mp = [dl.TileLayer()]
    mp.append(dl.Circle(center=kw_latlon, radius=boundary))

    # Create map centralised on search keyword
    selected_kw_layer = dl.DivMarker(position=kw_latlon,
                                     children=hf.popup_tooltip(kw_add),
                                     iconOptions=hse_icon)
    mp.append(selected_kw_layer)

    # Subway
    mp, final_msg = hf.create_location_map_layer(
        df=mrt_df, search_pt=kw_latlon, boundary=boundary,
        icon_fun=train_icon, icon_color='red', final_msg=final_msg,
        map_feature_list=mp, marker_name="MRT stations")

    # Attractions
    mp, final_msg = hf.create_location_map_layer(
        df=att_df, search_pt=kw_latlon, boundary=boundary,
        icon_fun=att_icon, icon_color='blue', final_msg=final_msg,
        map_feature_list=mp, marker_name="Attractions")

    result_table = dcc.Markdown(final_msg, dangerously_allow_html=True)
    map_output = dl.Map([dl.LayersControl(mp)], center=kw_latlon,
                        zoom=zoom_val, id='map', style={'height': '70vh',
                                                        'width': '80vh'})
    return map_output, result_table


if __name__ == '__main__':
    app.run_server()

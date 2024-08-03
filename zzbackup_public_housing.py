from dash import Dash, html, dcc, Input, Output, callback, State
import dash_bootstrap_components as dbc
from utils import data_process as dp
import plotly.graph_objects as go
from dotenv import load_dotenv
from datetime import datetime
import dash_ag_grid as dag
import pandas as pd
import numpy as np
import warnings
import requests
import json
warnings.simplefilter(action="ignore", category=FutureWarning)

# Simple parameter to trigger mongoDB instead of using local storage
load_dotenv()
api_calls = False
if api_calls:
    current_mth = datetime.now().date().strftime("%Y-%m")
    total_periods = [str(i)[:7] for i in pd.date_range(
        "2024-01-01", current_mth + "-01", freq='MS').tolist()]
    recent_periods = total_periods[-6:]

    df_cols = ['month', 'town', 'flat_type', 'block', 'street_name',
               'storey_range', 'floor_area_sqm', 'remaining_lease',
               'resale_price']
    param_fields = ",".join(df_cols)
    base_url = "https://data.gov.sg/api/action/datastore_search?resource_id="
    ext_url = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"
    full_url = base_url + ext_url

    recent_df = pd.DataFrame()
    for period in recent_periods:
        params = {
            "fields": param_fields,
            "filters": json.dumps({'month': period}),
            "limit": 10000
        }
        response = requests.get(full_url, params=params)
        mth_df = pd.DataFrame(response.json().get("result").get("records"))
        recent_df = pd.concat([recent_df, mth_df], axis=0)

    # Data Processing
    df = recent_df.copy()
    df.columns = ['month', 'town', 'flat', 'block', 'street_name',
                  'storey_range', 'area', 'lease_mths', 'price']

    df = dp.process_df_lease_left(df)
    df = dp.process_df_flat(df)

    df['storey_range'] = [i.replace(' TO ', '-') for i in df['storey_range']]
    df['area'] = df['area'].astype(np.float16)
    df['price'] = df['price'].astype(np.float32)

    df = df[['month', 'town', 'flat', 'block', 'street_name', 'storey_range',
             'area', 'lease_mths', 'price']]

    print("Completed data extraction from data.gov.sg")

else:
    # Load data through MongoDB, but I am mindful of storage and costs
    df = pd.read_csv("data/local_df.csv")


# Initalise App
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    requests_pathname_prefix="/public_housing/",
)

towns = df.town.unique().tolist()
towns.sort()
towns = ["All",] + towns

flat_type_grps = df["flat"].unique().tolist()
flat_type_grps.sort()

# Data processing for visualisations
# May wanna use polar for lazy evaluation

df["count"] = 1

bins = [0, 300000, 500000, 800000, 1000000, 2000000]
labels = ["0-300k", "300-500k", "500-800k", "800k-1m", ">=1m"]
df["price"] = df["price"].astype(float)
df["price_grp"] = pd.cut(df["price"], bins=bins, labels=labels, right=False)

price_grps = df["price_grp"].unique().tolist()
price_grps.sort()

price_grps_dict = dict()
price_grps_dict[price_grps[0]] = "#8BC1F7"
price_grps_dict[price_grps[1]] = "#06C"
price_grps_dict[price_grps[2]] = "#4CB140"
price_grps_dict[price_grps[3]] = "#F0AB00"
price_grps_dict[price_grps[4]] = "#C9190B"

period = "month"
period_grps = df[period].unique().tolist()
price_max, price_min = df["price"].max(), df["price"].min()
area_max, area_min = df["area"].max(), df["area"].min()
legend = dict(orientation="h", yanchor="bottom", y=-0.26, xanchor="right", x=1)
chart_width, chart_height = 500, 450
table_cols = ["month", "town", "flat", "block", "street_name", "storey_range",
              "area", "lease_mths", "price"]


def df_filter(s_town, s_flat, price_range, area_range, data_json):
    """Standardised filtering of df for visualisations"""
    fdf = pd.read_json(data_json, orient="split")
    fdf = fdf[fdf.flat.isin(s_flat)]

    if s_town != "All":
        fdf = fdf[fdf.town == s_town]

    fdf = fdf[fdf["price"].between(price_range[0], price_range[1])]
    fdf = fdf[fdf["area"].between(area_range[0], area_range[1])]

    return fdf


app.layout = [
    html.Div(
        id="data-store",
        style={"display": "none"},
        children=df.to_json(date_format="iso", orient="split"),
    ),
    html.H1(
        children="Singapore Public Housing Search Tool",
        style={"textAlign": "left", "padding": "5px", "color": "#555"},
    ),
    html.P(
        """This data is Singapore public housing data taken from data.gov.sg.
        I built this tool with the aim of making our public housing data
        information more accessible to the general public.""",
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
            html.Label("Town"),
            html.Div(dcc.Dropdown(options=towns, value="All", id="town")),
        ],
        style={"display": "inline-block", "width": "45%", "padding": "10px"},
    ),
    html.Div(
        children=[
            html.Label("Flats"),
            html.Div(
                dcc.Dropdown(
                    multi=True, options=flat_type_grps, value=flat_type_grps,
                    id="flat"
                )
            ),
        ],
        style={"display": "inline-block", "width": "45%", "padding": "10px"},
    ),
    html.Div(
        children=[
            html.Label("Price Range - SGD"),
            dcc.RangeSlider(
                id="price_range",
                min=price_min,
                max=price_max,
                step=10000,
                value=[price_min, price_max],
                tooltip={
                    "placement": "bottom",
                    "always_visible": False,
                    "template": "$ {value}",
                },
                marks={
                    i: f"${str((i/1000000))}M"
                    for i in range(0, int(round(price_max)), 250000)
                },
            ),
        ],
        style={"display": "inline-block", "width": "45%", "padding": "10px"},
    ),
    html.Div(
        children=[
            html.Label("Area - Sq.M"),
            dcc.RangeSlider(
                id="area_range",
                min=area_min,
                max=area_max,
                step=1,
                value=[area_min, area_max],
                tooltip={"placement": "bottom", "always_visible": False},
                marks={i: f"{i}sq.m" for i in range(
                    0, int(round(area_max)), 25)},
            ),
        ],
        style={"display": "inline-block", "width": "45%", "padding": "10px"},
    ),
    # Text box to display dynamic content
    html.P(id="dynamic-text",
           style={"textAlign": "center", "padding-top": "15px"}),
    html.Div(
        [
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.H3(
                                "Filtered Public Housing Transactions",
                                style={
                                    "font-size": "15px",
                                    "textAlign": "left",
                                    "margin-top": "20px",
                                },
                            ),
                            dag.AgGrid(
                                id="price-table",
                                columnDefs=[
                                    {"field": x,
                                     "sortable": True} for x in table_cols
                                ],
                                rowData=df[table_cols].to_dict("records"),
                                className="ag-theme-balham",
                                columnSize="sizeToFit",
                                dashGridOptions={
                                    "pagination": True,
                                    "paginationAutoPageSize": True,
                                },
                            ),
                        ],
                        style={
                            "height": chart_height,
                            "width": 1200,
                            "padding": "5px",
                            "display": "inline-block",
                        },
                    ),
                ],
                style=dict(display="flex"),
            ),
            html.Div(
                children=[
                    dcc.Graph(id="g0", style={
                        "display": "inline-block", "width": "33%"}),
                    dcc.Graph(id="g1", style={
                        "display": "inline-block", "width": "33%"}),
                    dcc.Graph(id="g2", style={
                        "display": "inline-block", "width": "33%"}),
                ]
            ),
        ],
        style={
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "alignItems": "center",
            "minHeight": "100vh",
            "textAlign": "center",
        },
    ),
]


# Standardised Dash Input-Output states
input_list = [
    Input("town", "value"),
    Input("flat", "value"),
    Input("price_range", "value"),
    Input("area_range", "value")
]

state_list = State('data-store', 'children')


@callback(Output("price-table", "rowData"), input_list, state_list)
def update_table(s_town, s_flat, price_range, area_range, data_json):
    fdf = df_filter(s_town, s_flat, price_range, area_range, data_json)
    return fdf.to_dict("records")


@callback(Output("dynamic-text", "children"), input_list, state_list)
def update_text(s_town, s_flat, price_range, area_range, data_json):
    # Construct dynamic text content based on filter values

    fdf = df_filter(s_town, s_flat, price_range, area_range, data_json)

    dynamic_text = f"""<b>Selected Fields</b>:
    <b>Region</b>: {s_town} |
    <b>Prices</b>: ${fdf.price.min():,} - ${fdf.price.max():,} |
    <b>Area</b>: {fdf.area.min()}-{fdf.area.max()} Sq.M
    """
    return dcc.Markdown(dynamic_text, dangerously_allow_html=True)


@callback(Output("g0", "figure"), input_list, state_list)
def update_g0(s_town, s_flat, price_range, area_range, data_json):
    fdf = df_filter(s_town, s_flat, price_range, area_range, data_json)

    fig = go.Figure()
    for p in period_grps:
        fig.add_trace(
            go.Box(
                y=fdf[fdf[period] == p].price,
                name=str(p),
                boxpoints="outliers",
                marker_color="rgb(8,81,156)",
                line_color="rgb(8,81,156)",
            )
        )

    fig.update_layout(
        title="Public Home Price Distributions",
        yaxis={"title": "Home Prices"},
        xaxis={"title": "Months"},
        width=chart_width,
        height=chart_height,
        showlegend=False,
    )
    return fig


@callback(Output("g1", "figure"), input_list, state_list)
def update_g1(s_town, s_flat, price_range, area_range, data_json):
    fdf = df_filter(s_town, s_flat, price_range, area_range, data_json)

    for_plot = fdf.groupby([period, "price_grp"])["count"].sum().reset_index()
    fig = go.Figure()
    for i in price_grps:
        fig.add_trace(
            go.Bar(
                name=i,
                x=for_plot[for_plot.price_grp == i][period].tolist(),
                y=for_plot[for_plot.price_grp == i]["count"].tolist(),
                marker_color=price_grps_dict[i],
            )
        )

    fig.update_layout(
        barmode="stack",
        xaxis={"title": "Months"},
        yaxis={"title": "Count"},
        hovermode="x unified",
        title="Number of Public Homes Sold by Price Categories",
        width=chart_width,
        height=chart_height,
        legend=legend,
    )
    return fig


@callback(Output("g2", "figure"), input_list, state_list)
def update_g2(s_town, s_flat, price_range, area_range, data_json):
    fdf = df_filter(s_town, s_flat, price_range, area_range, data_json)

    plot_base = fdf.groupby(period)["count"].sum().reset_index()
    pg_plots = fdf.groupby([period, "price_grp"])["count"].sum().reset_index()
    plots_2 = pg_plots.merge(plot_base, on=period)
    plots_2.columns = [period, "price_grp", "count", "total"]
    plots_2["percent"] = [
        round(i * 100, 1) for i in plots_2["count"] / plots_2["total"]
    ]

    fig = go.Figure()
    for i in price_grps:
        fig.add_trace(
            go.Bar(
                name=i,
                x=plots_2[plots_2.price_grp == i][period].tolist(),
                y=plots_2[plots_2.price_grp == i]["percent"].tolist(),
                marker_color=price_grps_dict[i],
            )
        )
    fig.add_hline(y=50, line_width=1.5, line_dash="dash", line_color="purple")
    fig.update_layout(
        barmode="stack",
        title=" Percentage of Public Homes Sold by Price Categories",
        xaxis={"title": "Months"},
        yaxis={"title": "%"},
        hovermode="x unified",
        width=chart_width,
        height=chart_height,
        legend=legend,
    )
    return fig


if __name__ == "__main__":
    app.run(debug=True)

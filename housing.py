from dash import Dash, html, dcc, Input, Output, callback, State
from concurrent.futures import ThreadPoolExecutor, as_completed
import dash_bootstrap_components as dbc
from datetime import datetime, date
import plotly.graph_objects as go
import dash_ag_grid as dag
import polars as pl
import numpy as np
import requests
import json

table_cols = ['month', 'town', 'flat', 'street_name', 'storey_range',
              'lease_left', 'area_sqm', 'area_sqft', 'price_sqm',
              'price_sqft', 'price']


[{"field": x, "sortable": True} for x in table_cols]

ag_table_cols = [
    {"field": 'month', "sortable": True},
    {"field": 'town', "sortable": True},
    {"field": 'flat', "sortable": True},
    {"field": 'street_name', "sortable": True},
    {"field": 'storey_range', "sortable": True},
    {"field": 'lease_left', "sortable": True},
    {"field": 'area_sqm', "sortable": True},
    {"field": 'area_sqft', "sortable": True},
    {
        "field": 'price_sqm', "sortable": True,
        "valueFormatter": {"function": "d3.format('($,.2f')(params.value)"},
    },
    {
        "field": 'price_sqft', "sortable": True,
        "valueFormatter": {"function": "d3.format('($,.2f')(params.value)"},
    },
    {
        "field": 'price', "sortable": True,
        "valueFormatter": {"function": "d3.format('($,.2f')(params.value)"},
    }

]

# Simple parameter to trigger mongoDB instead of using local storage
# Get current month and recent periods
current_mth = datetime.now().date().strftime("%Y-%m")
total_periods = [str(i)[:7] for i in pl.date_range(
    datetime(2024, 1, 1),
    datetime.now(),
    interval='1mo',
    eager=True).to_list()]
recent_periods = total_periods[-6:]

# Define columns and URL
df_cols = ['month', 'town', 'flat_type', 'block', 'street_name',
           'storey_range', 'floor_area_sqm', 'remaining_lease',
           'resale_price']
param_fields = ",".join(df_cols)
base_url = "https://data.gov.sg/api/action/datastore_search?resource_id="
ext_url = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"
full_url = base_url + ext_url


# Function to make an API request
def fetch_data_for_period(period):
    params = {
        "fields": param_fields,
        "filters": json.dumps({'month': period}),
        "limit": 10000
    }
    response = requests.get(full_url, params=params)
    if response.status_code == 200:
        return pl.DataFrame(response.json().get("result").get("records"))
    else:
        return pl.DataFrame()  # Return empty DataFrame on error


# Use ThreadPoolExecutor to fetch data in parallel
recent_df = pl.DataFrame()
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(
        fetch_data_for_period, period): period for period in recent_periods}

    for future in as_completed(futures):
        mth_df = future.result()
        recent_df = pl.concat([recent_df, mth_df], how='vertical')

# Data Processing
df = recent_df.clone()
df.columns = ['month', 'town', 'flat', 'block', 'street_name', 'storey_range', 
              'area_sqm', 'lease_mths', 'price']

df = df.with_columns(
    pl.col('area_sqm').cast(pl.Float32),
    pl.col('price').cast(pl.Float32),
).with_columns(
    (pl.col("area_sqm") * 10.7639).alias('area_sqft'),
).with_columns(
    (pl.col("price") / pl.col("area_sqm")).alias('price_sqm'),
    (pl.col("price") / pl.col('area_sqft')).alias("price_sqft"),
    ("BLK " + pl.col('block') + " " +
        pl.col("street_name")).alias("street_name"),
    pl.col('lease_mths').str.replace(
        " year", "y").str.replace(
        " month", "m").str.replace(
        " years", "y").str.replace(
        " months", 'm').alias(
        'lease_mths'),
    pl.col('flat').str.replace(
        " ROOM", "RM").str.replace(
        "EXECUTIVE", 'EC').str.replace(
        "MULTI-GENERATION", "MG").alias(
        'flat'),
    pl.col("storey_range").str.replace(" TO ", "-").alias("storey_range")
).rename({"lease_mths": "lease_left"}).drop("block")
df = df[table_cols]
print("Completed data extraction from data.gov.sg")

# Initalise App
app = Dash(
    __name__,
    external_stylesheets=[
        {'src': 'https://cdn.tailwindcss.com'},
        dbc.themes.BOOTSTRAP,
    ],
    requests_pathname_prefix="/housing/",
)

# Chart parameters
towns = df.select("town").unique().to_series().to_list()
towns.sort()
towns = ["All",] + towns

flat_type_grps = df.select("flat").unique().to_series().to_list()
flat_type_grps.sort()

period_grps = df.select("month").unique().to_series().to_list()
price_max = df.select("price").max().rows()[0][0]
price_min = df.select("price").min().rows()[0][0]
area_max = df.select("area_sqm").max().rows()[0][0]
area_min = df.select("area_sqm").min().rows()[0][0]

legend = dict(orientation="h", yanchor="bottom", y=-0.26, xanchor="right", x=1)
chart_width, chart_height = 500, 450


def df_filter(month, town, flat, area_type, max_area, min_area, price_type,
              max_price, min_price, min_lease, max_lease, street_name,
              data_json):
    """Standardised filtering of df for visualisations"""

    # Using Pandas and converting it to Polars, as my pl.read_json has issues
    df = pl.DataFrame(json.loads(data_json))

    yr = datetime.now().year
    mth = datetime.now().month
    selected_mths = pl.date_range(
        date(2024, 1, 1), date(yr, mth, 1), "1mo", eager=True).to_list()
    selected_mths = [i.strftime("%Y-%m") for i in selected_mths[-int(month):]]

    df = df.filter(
        pl.col("month").is_in(selected_mths),
        pl.col("flat").is_in(flat)
    )

    if street_name:
        df = df.filter(pl.col("street_name").str.contains(street_name.upper()))

    df = df.with_columns(
        pl.col("lease_left")
        .str.split_exact("y", 1)
        .struct.rename_fields(["year_count", "mth_count"])
        .alias("fields")
    ).unnest("fields")

    df = df.with_columns(pl.col('year_count').cast(pl.Int32))

    if max_lease:
        df = df.filter(pl.col("year_count") <= int(max_lease))

    if min_lease:
        df = df.filter(pl.col("year_count") >= int(min_lease))

    area_type = "area" if area_type == "Sq M" else "area_sqft"
    price_type = "price" if price_type == "Price" else "price_sqft"

    if town != "All":
        df = df.filter(pl.col("town") == town)

    if max_price:
        df = df.filter(pl.col(price_type) <= max_price)

    if min_price:
        df = df.filter(pl.col(price_type) >= min_price)

    if max_area:
        df.filter(pl.col(area_type) <= max_area)

    if min_area:
        df = df.filter(pl.col(area_type) >= min_area)

    print("Filter applied")
    return df


def labels_for_charts(df: pl.DataFrame, 
                      area_type: str,
                      base_cols = ['price', 'town', 'street_name']):
    """ Takes pl.DataFrames and returns the parameters for Plotly charts """

    price_area = "price_sqft" if area_type != "Sq M" else "price_sqm"
    price_label = "Sq Ft" if area_type != "Sq M" else "Sq M"

    area_label = "area_sqm" if area_type != "Sq M" else "area_sqft"
    base_cols = base_cols + [area_label,]
    customdata_set = list(df[base_cols].to_numpy())

    return price_area, price_label, customdata_set


app.layout = html.Div([
    html.Div(
        id="data-store",
        style={"display": "none"},
        children=df.write_json(),
    ),
    html.H3(
        children="These are Homes, Truly",
        style={'font-weight': 'bold', 'font-size': '26px'},
        className="mb-4 pt-4 px-4",
    ),
    dcc.Markdown(
        """
        Explore Singapore's most recent past public housing transactions
        effortlessly with our site! Updated daily with data from data.gov.sg,
        our tool allows you access to the latest information public housing
        resale data provided by HDB. Currently, the data is taken as is, and
        may not reflect the latest public housing transactions reported by the
        media.

        I built this tool to help anyone who wants to research on the Singapore
        public housing resale market, whether you're a prospective buyer,
        seller, or someone just curious about how much your neighbours are
        selling their public homes! Beyond a table of transactions, I included
        a scatter plot to compare home prices with price per sq metre / feet
        and a boxplot distribution of home prices or price per sq metre / feet.

        **This website is best view on a desktop, because doing property
        research on your phone will be such a pain!**

        *Also, if you are interested general Singapore public housing resale
        market trends of the past few years, visit my other dashboard @ [Public
        Home Trends](https://sg-housing.onrender.com/sg-public-home-trends),
        where I share broader public housing resale trends, outliers and price
        category breakdowns.*""",
        className="px-4",
    ),
    dbc.Row([
        dbc.Col(
            dbc.Button(
                "Filters",
                id="collapse-button",
                className="mb-3",
                color="danger",
                n_clicks=0,
                style={"verticalAlign": "top"}
            ),
            width="auto"
        ),
        dbc.Col(
            dcc.Loading([
                html.P(
                    id="dynamic-text",
                    style={"textAlign": "center", "padding-top": "10px"}
                )]),
            width="auto"
        ),
        dbc.Col(
            dbc.Button(
                "Caveats",
                id="collapse-caveats",
                className="mb-3",
                color="danger",
                n_clicks=0,
                style={"verticalAlign": "top"}
            ),
            width="auto"
        ),
    ], justify="center"),
    dbc.Collapse(
        dbc.Card(
            dbc.CardBody([
                dcc.Markdown("""
                1. Area provided by HDB is in square metres. Calculations for
                square feet are done by taking square metres by 10.7639.
                2. Lease left is calculated from remaining lease provided by
                HDB.
                3. Data is taken from HDB as is. This data source seems
                slower that transactions reported in the media.
                4. Information provided here is only meant for research, and
                shouldn't be seen as financial advice.""")
            ], style={"textAlign": "left", "color": "#555", "padding": "5px"}),
        ),
        id="caveats",
        is_open=False,
    ),
    dbc.Collapse(
        dbc.Card(dbc.CardBody([
            html.Div([
                html.Div([
                    html.Label("Months"),
                    dcc.Dropdown(options=[3, 6], value=6, id="month")
                ], style={"display": "inline-block",
                          "width": "7%", "padding": "10px"},
                ),
                html.Div([
                    html.Label("Town"),
                    html.Div(dcc.Dropdown(
                        options=towns, value="All", id="town")),
                ], style={"display": "inline-block",
                          "width": "18%", "padding": "10px"},
                ),
                html.Div([
                    html.Label("Housing"),
                    dcc.Dropdown(multi=True, options=flat_type_grps,
                         value=flat_type_grps, id="flat"),
                ], style={"display": "inline-block",
                          "width": "38%", "padding": "10px"},
                ),
                html.Div([
                    html.Label("Min Lease [Yrs]"),
                    dcc.Input(type="number",
                              placeholder="Add No.",
                              style={"display": "flex",
                                     "border-color": "#E5E4E2",
                                     "padding": "5px"},
                              id="min_lease"),
                ], style={"display": "flex",  "flexDirection": "column",
                          "width": "12%", "padding": "10px",
                          "verticalAlign": "top"}),
                html.Div([
                    html.Label("Max Lease [Yrs]"),
                    dcc.Input(type="number",
                              placeholder="Add No.",
                              style={"display": "flex",
                                     "border-color": "#E5E4E2",
                                     "padding": "5px"},
                              id="max_lease"),
                ], style={"display": "flex",  "flexDirection": "column",
                          "width": "12%", "padding": "10px",
                          "verticalAlign": "top"},
                )
            ], style={"display": "flex", "flexDirection": "row",
                      "alignItems": "center"}
            ),
            # Area inputs
            html.Div([
                html.Div([
                    html.Label("Sq Feet | Sq M"),
                    html.Div(dcc.Dropdown(options=['Sq M', "Sq Feet"],
                                          value="Sq Feet", id="area_type")),
                ], style={"display": "flex", "flexDirection": "column",
                          "width": "12%", "padding": "10px"},
                ),
                html.Div([
                    html.Label("Min Area"),
                    dcc.Input(type="number",
                              placeholder="Add No.",
                              style={"display": "inline-block",
                                     "border-color": "#E5E4E2",
                                     "padding": "5px"},
                              id="min_area"),
                ], style={"display": "flex",  "flexDirection": "column",
                          "width": "12%", "padding": "5px"},
                ),
                html.Div([
                    html.Label("Max Area"),
                    dcc.Input(type="number",
                              placeholder="Add No.",
                              style={"display": "inline-block",
                                     "border-color": "#E5E4E2",
                                     "padding": "5px"},
                              id="max_area"),
                ], style={"display": "flex", "flexDirection": "column",
                          "width": "12%", "padding": "5px"},
                ),
                html.Div([
                    html.Label("Price | Price Per Area"),
                    dcc.Dropdown(options=['Price', "Price / Area"],
                         value="Price", id="price_type"),
                ], style={"display": "flex", "flexDirection": "column",
                          "width": "12%", "padding": "5px"},
                ),
                html.Div([
                    html.Label("Min Price | Price Per Area"),
                    dcc.Input(type="number",
                              placeholder="Add No.",
                              style={"display": "inline-block",
                                     "border-color": "#E5E4E2",
                                     "padding": "5px"},
                              id="min_price"),
                ], style={"display": "flex", "flexDirection": "column",
                          "width": "15%", "padding": "5px"},
                ),
                html.Div([
                    html.Label("Max Price | Price / Area"),
                    dcc.Input(type="number",
                              style={"display": "inline-block",
                                     "border-color": "#E5E4E2",
                                     "padding": "5px"},
                              placeholder="Add No.",
                              id="max_price"),
                ], style={"display": "flex", "flexDirection": "column",
                          "width": "15%", "padding": "5px"},
                ),
                html.Div([
                    html.Label("Submit"),
                    html.Button('Submit', id='submit-button',
                                style={"display": "inline-block",
                                       "border-color": "#E5E4E2",
                                       "padding": "5px"},
                                )
                ], style={"display": "flex", "flexDirection": "column",
                          "width": "8%", "padding": "5px"},
                )
            ], style={"display": "flex", "flexDirection": "row",
                      "alignItems": "center"}),
            html.Div([
                html.Label("""Search by Street Name
        ( Add | separator to include >1 street name )"""),
                dcc.Input(type="text",
                          style={"display": "inline-block",
                                 "border-color": "#E5E4E2",
                                 "padding": "5px"},
                          placeholder="Type the Street Name here",
                          id="street_name"),
            ], style={"display": "flex", "flexDirection": "column",
                      "width": "45%", "padding": "5px"},
            ),
        ]
        )),
        id="collapse",
        is_open=True,
    ),
    # Text box to display dynamic content
    html.Div([
        html.Div([
            dcc.Loading([
                html.Div([
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
                        columnDefs=ag_table_cols,
                        rowData=df.select(table_cols).to_dicts(),
                        className="ag-theme-balham",
                        columnSize="responsiveSizeToFit",
                        dashGridOptions={
                            "pagination": True,
                            "paginationAutoPageSize": True,
                        },
                    ),
                ], style={
                    "height": chart_height,
                    "width": 1200,
                    "padding": "5px",
                    "display": "inline-block",
                },
                )])
        ], style=dict(display="flex"),
        ),
        dcc.Loading([
            html.Div([
                dcc.Graph(id="g0", style={
                    "display": "inline-block", "width": "30%"}),
                dcc.Graph(id="g2", style={
                    "display": "inline-block", "width": "30%"}),
                dcc.Graph(id="g1", style={
                    "display": "inline-block", "width": "30%"}),
            ]
            )])
    ],
        style={"display": "flex",
               "flexDirection": "column",
               "justifyContent": "center",
               "alignItems": "center",
               "minHeight": "100vh",
               "textAlign": "center",
               }
    )
])


# Standardised Dash Input-Output states
new_input_list = Input('submit-button', 'n_clicks'),
new_state_list = [
    State('month', 'value'),
    State('town', 'value'),
    State('flat', 'value'),
    State('area_type', 'value'),
    State('max_area', 'value'),
    State('min_area', 'value'),
    State('price_type', 'value'),
    State('max_price', 'value'),
    State('min_price', 'value'),
    State('max_lease', 'value'),
    State('min_lease', 'value'),
    State('street_name', 'value'),
    State('data-store', 'children')
]


@callback(Output("price-table", "rowData"), new_input_list, new_state_list)
def update_table(n_clicks, month, town, flat, area_type, max_area, min_area,
                 price_type, max_price, min_price, max_lease, min_lease,
                 street_name, data_json):
     
    df = df_filter(month, town, flat, area_type, max_area, min_area,
                    price_type, max_price, min_price, max_lease, min_lease,
                    street_name, data_json)

    records = df.shape[0]
    print(month, town, flat, area_type, max_area, min_area,
          price_type, max_price, min_price, max_lease, min_lease,
          street_name, records)

    df = df.with_columns(
        pl.col('area_sqft').round(2),
        pl.col('price_sqm').round(2),
        pl.col('price_sqft').round(2),
        pl.col('price').cast(pl.Float64).round(2),
    )
    return df.to_dicts()


@callback(Output("dynamic-text", "children"), new_input_list, new_state_list)
def update_text(n_clicks, month, town, flat, area_type, max_area, min_area,
                price_type, max_price, min_price, max_lease, min_lease,
                street_name, data_json):
    # Construct dynamic text content based on filter values

    df = df_filter(month, town, flat, area_type, max_area, min_area,
                    price_type, max_price, min_price, max_lease, min_lease,
                    street_name, data_json)

    records = df.shape[0]

    if records > 0:
        if price_type == 'Price' and area_type == 'Sq M':
            price_min = min(df.select("price").to_series())
            price_max = max(df.select("price").to_series())

            area_min = min(df.select("area_sqm").to_series())
            area_max = max(df.select("area_sqm").to_series())

        elif price_type == 'Price' and area_type == 'Sq Feet':
            price_min = min(df.select("price").to_series())
            price_max = max(df.select("price").to_series())

            area_min = min(df.select("area_sqft").to_series())
            area_max = max(df.select("area_sqft").to_series())

        elif price_type == "Price / Area" and area_type == "Sq M":
            price_min = min(df.select("price_sqm").to_series())
            price_max = max(df.select("price_sqm").to_serise())

            area_min = min(df.select("area_sqm").to_series())
            area_max = max(df.select("area_sqm").to_series())

            price_type = 'Price / Sq M'

        elif price_type == "Price / Area" and area_type == "Sq Feet":
            price_min = min(df.select("price_sqft").to_series())
            price_max = max(df.select("price_sqft").to_series())

            area_min = min(df.select("area_sqft").to_series())
            area_max = max(df.select("area_sqft").to_series())

            price_type = 'Price / Sq Feet'

        text = f"""<b>You searched : </b>
        <b>Town</b>: {town} |
        <b>{price_type}</b>: ${price_min:,} - ${price_max:,} |
        <b>{area_type}</b>: {area_min:,} - {area_max:,}
        """

        if min_lease and max_lease:
            text += f" | <b>Lease from</b> {min_lease:,} - {max_lease:,}"
        elif min_lease:
            text += f" | <b>Lease >= </b> {min_lease:,}"
        elif max_lease:
            text += f" | <b>Lease =< </b> {max_lease:,}"

        text += f" | <b>Total records</b>: {records:,}"
    else:
        text = "<b>Your search returned no results</b>"

    return dcc.Markdown(text, dangerously_allow_html=True)


@callback(Output("g0", "figure"), new_input_list, new_state_list)
def update_g0(n_clicks, month, town, flat, area_type, max_area, min_area,
              price_type, max_price, min_price, max_lease, min_lease,
              street_name, data_json):
    df = df_filter(month, town, flat, area_type, max_area, min_area,
                    price_type, max_price, min_price, max_lease, min_lease,
                    street_name, data_json)

    price_area, price_label, label_data = labels_for_charts(df, area_type)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            y=df.select('price').to_series(),  # unchanged
            x=df.select(price_area).to_series(),
            customdata=label_data,
            hovertemplate='<i>Price:</i> %{y:$,}<br>' +
            '<i>Area:</i> %{customdata[3]:,}<br>' +
            '<i>Price/Area:</i> %{x:$,}<br>' +
            '<i>Town :</i> %{customdata[0]}<br>' +
            '<i>Street Name:</i> %{customdata[1]}<br>' +
            '<i>Lease Left:</i> %{customdata[2]}',
            mode='markers',
            marker_color="rgb(8,81,156)",
        )
    )
    fig.update_layout(
        title=f"Home Prices vs Prices / {price_label}",
        yaxis={"title": "Home Prices"},
        xaxis={"title": f"Prices / {price_label}"},
        width=chart_width,
        height=chart_height,
        showlegend=False,
    )
    return fig


@callback(Output("g2", "figure"), new_input_list, new_state_list)
def update_g2(n_clicks, month, town, flat, area_type, max_area, min_area,
              price_type, max_price, min_price, max_lease, min_lease,
              street_name, data_json):
    df = df_filter(month, town, flat, area_type, max_area, min_area,
                    price_type, max_price, min_price, max_lease, min_lease,
                    street_name, data_json)

    price_area, price_label, label_data = labels_for_charts(df, area_type)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            y=df.select(price_area).to_series(),  # unchanged
            x=df.select('year_count').to_series(),
            customdata=label_data,
            hovertemplate='<i>Price/' + price_label + ':</i> %{y:$,}<br>' +
            '<i>Price:</i> %{customdata[0]:$,}<br>' +
            '<i>Area:</i> %{customdata[3]:,}<br>' +
            '<i>Town :</i> %{customdata[1]}<br>' +
            '<i>Street Name:</i> %{customdata[2]}<br>' +
            '<i>Lease Left:</i> %{x}',
            mode='markers',
            marker_color="rgb(8,81,156)",
        )
    )
    fig.update_layout(
        title=f"[ Price / {price_label} ] VS [ Lease Left ]",
        yaxis={"title": f"Price / {price_label}"},
        xaxis={"title": "Lease Left"},
        width=chart_width,
        height=chart_height,
        showlegend=False,
    )

    fig.update_xaxes(showspikes=True)
    fig.update_yaxes(showspikes=True)

    return fig


@callback(Output("g1", "figure"), new_input_list, new_state_list)
def update_g1(n_clicks, month, town, flat, area_type, max_area, min_area,
              price_type, max_price, min_price, max_lease, min_lease,
              street_name, data_json):

    df = df_filter(month, town, flat, area_type, max_area, min_area,
                    price_type, max_price, min_price, max_lease, min_lease,
                    street_name, data_json)

    if price_type == "Price":
        price_value = price_type.lower()
        price_label = "Price"

    else:
        price_value = "price_sqft" if area_type != "Sq M" else "price_sqm"
        price_label = "Price / Sq Ft" if area_type != "Sq M" else "Price / Sq M"

    fig = go.Figure()
    fig.add_trace(
        go.Box(
            y=df.select(price_value).to_series(),
            name="Selected Homes",
            boxpoints="outliers",
            marker_color="rgb(8,81,156)",
            line_color="rgb(8,81,156)",
        )
    )
    fig.update_layout(
        title=f"Home {price_label} Distributions",
        yaxis={"title": f"{price_label}"},
        width=chart_width,
        height=chart_height,
        showlegend=False,
    )
    return fig


@callback(
    Output("collapse", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("caveats", "is_open"),
    [Input("collapse-caveats", "n_clicks")],
    [State("caveats", "is_open")],
)
def toggle_caveat(n, is_open):
    if n:
        return not is_open
    return is_open


if __name__ == "__main__":
    app.run(debug=True)

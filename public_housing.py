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
with ThreadPoolExecutor(max_workers=4) as executor:
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
        "s", "").str.replace(
        " year", "y").str.replace(
        " month", "m").alias('lease_mths'),
    pl.col('flat').str.replace(
        " ROOM", "RM").str.replace(
        "EXECUTIVE", 'EC').str.replace(
        "MULTI-GENERATION", "MG").alias('flat'),
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
    requests_pathname_prefix="/public_housing/",
)

# Chart parameters
towns = df.select("town").unique().to_series().to_list()
towns.sort()
towns = ["All",] + towns

flat_type_grps = df.select("flat").unique().to_series().to_list()
flat_type_grps.sort()

final_flat_type_grps = []
for flat in flat_type_grps:
    final_flat_type_grps.append({
        "label": html.Span([flat], style={'background-color': "#FFC0BD",
                                          'border': "#FFC0BD",
                                          'color': 'black'}),
        "value": flat, "search": flat
    })

period_grps = df.select("month").unique().to_series().to_list()
price_max = df.select("price").max().rows()[0][0]
price_min = df.select("price").min().rows()[0][0]
area_max = df.select("area_sqm").max().rows()[0][0]
area_min = df.select("area_sqm").min().rows()[0][0]

yr, mth = datetime.now().year, datetime.now().month
selected_mths = pl.date_range(
    date(2024, 1, 1), date(yr, mth, 1), "1mo", eager=True).to_list()

legend = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=.5)
chart_width, chart_height = 680, 550

def convert_price_area(price_type, area_type):
    """ Convert user price & area inputs into usable table ftilers & 
    Plotly labels """ 

    if price_type != 'price':
        price_type = 'price_sqft' if area_type == 'area_sqft' else 'price_sqm'

    return price_type


def grid_format(table: pl.DataFrame):
    """ Add custom formatting to AGrid Table Outputs """
    output = [
        {"field": "month", "sortable": True, 'width': 100, 'maxWidth': 100},
        {"field": "flat", "sortable": True, 'width': 70, 'maxWidth': 70},
        {"field": "town", "sortable": True, 'width': 180, 'maxWidth': 300},
        {"field": "street_name", "sortable": True, 'width': 380, 'maxWidth': 800},
        {"field": "storey_range", "sortable": True, 'width': 130, 'maxWidth': 130},
        {"field": "lease_left", "sortable": True, 'width': 100, 'maxWidth': 100},
        {"field": "price", "sortable": True, 'width': 150, 'maxWidth': 200, 
         "valueFormatter": {"function": "d3.format('($,.2f')(params.value)"},
        }
    ]
    for col in table.columns:
        if 'price_' in col:
            output.append({
                "field": col, "sortable": True, 'width': 120, 'maxWidth': 120,
                "valueFormatter": {"function":
                                   "d3.format('($,.2f')(params.value)"},
            })
        elif "area" in col:
            output.append({
                "field": col, "sortable": True, 'width': 120, 'maxWidth': 120,
                "valueFormatter": {"function":
                                   "d3.format('(,.2f')(params.value)"},
            })

    return output


def df_filter(month, town, flat, area_type, max_area, min_area, price_type,
              max_price, min_price, min_lease, max_lease, street_name, yr, mth,
              selected_mths, data_json):
    """Filter Polars DataFrame for Viz, based on inputs"""

    # Using Pandas and converting it to Polars, as my pl.read_json has issues
    df = pl.DataFrame(json.loads(data_json))

    selected_mths = [i.strftime("%Y-%m") for i in selected_mths[-int(month):]]

    df = df.with_columns(
        pl.col("lease_left")
        .str.split_exact("y", 1)
        .struct.rename_fields(["year_count", "mth_count"])
        .alias("fields")
    ).unnest("fields").with_columns(
        pl.col('year_count').cast(pl.Int32))

    if max_lease:
        df = df.with_columns(
            pl.when(pl.col("year_count") <= int(max_lease))
            .then(True)
            .otherwise(False)
            .alias("max_lease_flag")
        )

    if min_lease:
        df = df.with_columns(
            pl.when(pl.col("year_count") >= int(min_lease))
            .then(True)
            .otherwise(False)
            .alias("min_lease_flag")
        )

    df = df.with_columns(
        pl.when(
            pl.col("month").is_in(selected_mths),
            pl.col("flat").is_in(flat)
        )
        .then(True)
        .otherwise(False)
        .alias("month_flat_flag")
    )

    if street_name:
        df = df.with_columns(
            pl.when(pl.col("street_name").str.contains(street_name.upper()))
            .then(True)
            .otherwise(False)
            .alias("street_name_flag")
        )

    price_type = convert_price_area(price_type, area_type)

    # Filter for Sq Ft or Sq M columns
    if area_type == 'area_sqft':
        df = df.drop("price_sqm", 'area_sqm')
    else:
        df = df.drop('price_sqft', "area_sqft")

    if town != "All":
        df = df.with_columns(
            pl.when(pl.col("town") == town)
            .then(True)
            .otherwise(False)
            .alias("town_flag")
        )
    else:
        df = df.with_columns(town_flag = True)

    if max_price:
        df = df.with_columns(
            pl.when(pl.col(price_type) <= max_price)
            .then(True)
            .otherwise(False)
            .alias("max_price_flag")
        )

    if min_price:
        df = df.with_columns(
            pl.when(pl.col(price_type) >= min_price)
            .then(True)
            .otherwise(False)
            .alias("min_price_flag")
        )

    if max_area:
        df = df.with_columns(
            pl.when(pl.col(area_type) <= min_area)
            .then(True)
            .otherwise(False)
            .alias("max_area_flag")
        )

    if min_area:
        df = df.with_columns(
            pl.when(pl.col(area_type) >= min_area)
            .then(True)
            .otherwise(False)
            .alias("min_area_flag")
        )

    return df


app.layout = html.Div([
    html.Div(
        id="data-store",
        style={"display": "none"},
        children=df.write_json(),
    ),
    dcc.Store(id='filtered-data'),
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
        market trends of the past few years, visit my other dashboard @ **Public
        Home Trends ( Above )**, where I share broader public housing resale 
        trends, outliers and price category breakdowns.*""",
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
                )], type="circle", color="rgb(220, 38, 38)"),
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
                2. Lease left is calculated from remaining lease provided by HDB.
                3. Data is taken from HDB as is. This data source seems
                slower that transactions reported in the media.
                4. Information provided here is only for research, and
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
                    html.Label("Flat"),
                    dcc.Dropdown(multi=True, options=final_flat_type_grps,
                                 value=flat_type_grps,
                                 id="flat"),
                ], style={"display": "inline-block",
                          "width": "40%", "padding": "10px"},
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
                    html.Div(dcc.Dropdown(options=[
                        {'label': 'Sq Feet', 'value': 'area_sqft'},
                        {'label': 'Sq M', 'value': 'area_sqm'},
                        ], value="area_sqft", id="area_type")),
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
                    html.Label("Price | Price / Area"),
                    dcc.Dropdown(options=[
                        {"label": 'Price', "value": 'price'},
                        {"label": "Price / Area", "value": 'price_area'}
                    ], value="price", id="price_type"),
                ], style={"display": "flex", "flexDirection": "column",
                          "width": "14%", "padding": "5px"},
                ),
                html.Div([
                    html.Label("Min [ Price | Price / Area ]"),
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
                    html.Label("Max [ Price | Price / Area ]"),
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
                    html.Label("Submit", style={'margin-top': '12px'}),
                    dbc.Button('Submit', 
                               id='submit-button',
                               className="mb-3",
                               color="danger",
                               n_clicks=0,
                               style={"verticalAlign": "top"})
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
                            "font-size": "20px",
                            "textAlign": "left",
                            "margin-top": "15px",
                            "margin-bottom": "5px",
                        },
                    ),
                    dag.AgGrid(
                        id="price-table",
                        columnDefs=grid_format(df),
                        rowData=df.to_dicts(),
                        className="ag-theme-balham",
                        columnSize="responsiveSizeToFit",
                        dashGridOptions={
                            "pagination": True,
                            "paginationAutoPageSize": True,
                        },
                    ),
                ], style={
                    "height": 450,
                    "width": 1200,
                    # "padding": "5px",
                    "display": "inline-block",
                },
                )], type="circle", color="rgb(220, 38, 38)"),
        ], style=dict(display="flex"),
        ),
        dcc.Loading([
            html.Div([
                dcc.Graph(id="g0", style={"display": "inline-block", "width": "48%"}),
                dcc.Graph(id="g2", style={"display": "inline-block", "width": "38%"}),
            ], style={
                "display": "flex",
                "justify-content": "flex-start",
                "width": "100%"}
            )], type="circle", color="rgb(220, 38, 38)")
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
basic_state_list = [
    State('town', 'value'),
    State('area_type', 'value'),
    State('price_type', 'value'),
    State('max_lease', 'value'),
    State('min_lease', 'value')
]
add_on_state_list = [
    State('month', 'value'),
    State('flat', 'value'),
    State('max_area', 'value'),
    State('min_area', 'value'),
    State('max_price', 'value'),
    State('min_price', 'value'),
    State('street_name', 'value'),
    State('data-store', 'children')
]
full_state_list = basic_state_list + add_on_state_list

@callback(Output("filtered-data", "data"),
          Input('submit-button', 'n_clicks'), 
          full_state_list)
def filtered_data(n_clicks, town, area_type, price_type, max_lease, min_lease,
                  month, flat, max_area, min_area, max_price, min_price, 
                  street_name, data_json):

    return df_filter(month, town, flat, area_type, max_area, min_area, 
                     price_type, max_price, min_price, max_lease, min_lease,
                     street_name, yr, mth, selected_mths, data_json).to_dicts()


@callback(Output("price-table", "rowData"),
          Output('price-table', 'columnDefs'),
          Input('filtered-data', 'data'),
          State('area_type', 'value'),
          State('price_type', 'value'))
def update_table(data, area_type, price_type):
    """ Table output to show all searched transactions """
    output = [{}]
    df = pl.DataFrame(data).drop("year_count", "mth_count")
    if df is not None:
        flags = [i for i in df.columns if 'flag' in i]
        df = df.filter(
                ~pl.any_horizontal(pl.col('*') == False)
            ).drop(flags)

        output = df.to_dicts()
        columnDefs=grid_format(df)

    return output, columnDefs


@callback(Output("dynamic-text", "children"),
          Input('filtered-data', 'data'),
          basic_state_list)
def update_text(data, town, area_type, price_type, max_lease, min_lease):
    """ Summary text for searched output """

    df = pl.DataFrame(data)

    flags = [i for i in df.columns if 'flag' in i]
    df = df.filter(
        ~pl.any_horizontal(pl.col('*') == False)
    ).drop(flags)

    records = df.shape[0]
    if records > 0:

        area_min = min(df.select(area_type).to_series())
        area_max = max(df.select(area_type).to_series())

        if price_type == 'price':
            price_min = min(df.select(price_type).to_series())
            price_max = max(df.select(price_type).to_series())
            price_label = 'price'
        
        else:
            price_type = "price_" + area_type.split('_')[-1]
            price_min = min(df.select(price_type).to_series())
            price_max = max(df.select(price_type).to_series())
            price_label = f"Price / {area_type.split('_')[-1]}"

        text = f"""<b>You searched : </b>
        <b>Town</b>: {town} |
        <b>{price_label}</b>: ${price_min:,} - ${price_max:,} |
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
        text = "<b><< YOUR SEARCH HAS NO RESULTS >></b>"

    return dcc.Markdown(text, dangerously_allow_html=True)


@callback(Output("g0", "figure"),
          Input('filtered-data', 'data'),
          basic_state_list)
def update_g0(data, town, area_type, price_type, max_lease, min_lease):
    """ Scatter Plot of Price to Price / Sq Area """
    fig = go.Figure()

    df = pl.DataFrame(data)

    if df is not None:
        flags = [i for i in df.columns if 'flag' in i]
        non_df = df.filter(pl.any_horizontal(pl.col('*') == False)).drop(flags)
        df = df.filter(~pl.any_horizontal(pl.col('*') == False)).drop(flags)

        price_type = convert_price_area(price_type, area_type)

        df = df.with_columns(
            pl.col(price_type).round(2),
            pl.col(area_type).round(2),
        )

        base_cols = ['year_count', 'town', 'street_name', area_type]
        customdata_set = list(df[base_cols].to_numpy())

        fig.add_trace(
            go.Scattergl(
                y=non_df.select('price').to_series(),  # unchanged
                x=non_df.select(price_type).to_series(),
                mode='markers',
                hoverinfo='skip',
                marker={"color": "#FFC0BD", "opacity": 0.5},
                name='Rest of SG'
            ))
        fig.add_trace(
            go.Scattergl(
                y=df.select('price').to_series(),  # unchanged
                x=df.select(price_type).to_series(),
                customdata=customdata_set,
                hovertemplate='<i>Price:</i> %{y:$,}<br>' +
                '<i>Area:</i> %{customdata[3]:,}<br>' +
                '<i>Price/Area:</i> %{x:$,}<br>' +
                '<i>Town :</i> %{customdata[1]}<br>' +
                '<i>Street Name:</i> %{customdata[2]}<br>' +
                '<i>Lease Left:</i> %{customdata[0]}',
                mode='markers',
                marker={"color": "rgb(220, 38, 38)", "opacity": 0.9},
                name='Selected Data'
            ))
        fig.update_layout(
            title="<b>Home Prices vs Price / Area<b>",
            yaxis={"title": "price", "gridcolor" :'#d3d3d3', "showspikes": True},
            xaxis={"title": f"{price_type}", "gridcolor":'#d3d3d3', "showspikes": True},
            width=chart_width,
            height=chart_height,
            legend=legend,
            plot_bgcolor='white',
            margin=dict(l=5,r=5)
        )
    return fig


@callback(Output("g2", "figure"),
          Input('filtered-data', 'data'),
          basic_state_list)
def update_g2(data, town, area_type, price_type, max_lease, min_lease):
    """ Price to Lease Left Plot """
    fig = go.Figure()
    df = pl.DataFrame(data)

    if df is not None:
        flags = [i for i in df.columns if 'flag' in i]
        non_df = df.filter(pl.any_horizontal(pl.col('*') == False)).drop(flags)
        df = df.filter(~pl.any_horizontal(pl.col('*') == False)).drop(flags)

        # Transform user inputs into table usable columns
        price_type = convert_price_area(price_type, area_type)

        df = df.with_columns(
            pl.col(price_type).round(2),
            pl.col(area_type).round(2),
        )

        if area_type == "area_sqm":
            base_cols = ['price', 'price_sqm', 'town', 'street_name', area_type]
        else:
            base_cols = ['price', 'price_sqft', 'town', 'street_name', area_type]
        
        customdata_set = list(df[base_cols].to_numpy())
        
        fig.add_trace(
            go.Scattergl(
                y=non_df.select(price_type).to_series(),  # unchanged
                x=non_df.select("year_count").to_series(),
                mode='markers',
                hoverinfo='skip',
                marker={"color": "#FFC0BD", "opacity": 0.5},
                name='Rest of SG'
            ))

        fig.add_trace(
            go.Scattergl(
                y=df.select(price_type).to_series(),  # unchanged
                x=df.select('year_count').to_series(),
                customdata=customdata_set,
                hovertemplate='<i>Price:</i> %{customdata[0]:$,}<br>' +
                '<i>Area:</i> %{customdata[4]:,}<br>' +
                '<i>Price/Area:</i> %{customdata[1]:$,}<br>' +
                '<i>Town :</i> %{customdata[2]}<br>' +
                '<i>Street Name:</i> %{customdata[3]}<br>' +
                '<i>Lease Left:</i> %{x}',
                mode='markers',
                marker={"color": "rgb(220, 38, 38)", "opacity": 0.9},
                name="Selected Data"
            )
        )
        fig.update_layout(
            title="<b>Home Prices vs Lease Left<b>",
            yaxis={"title": f"{price_type}", 'gridcolor': '#d3d3d3', "showspikes": True},
            xaxis={"title": "lease_left", 'gridcolor': '#d3d3d3', "showspikes": True},
            width=chart_width,
            height=chart_height,
            legend=legend,
            plot_bgcolor='white',
            margin=dict(l=5,r=5)
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

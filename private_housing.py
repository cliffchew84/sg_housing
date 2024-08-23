
from dash import Dash, html, dcc, Input, Output, callback, State
from concurrent.futures import ThreadPoolExecutor, as_completed
import dash_bootstrap_components as dbc
from datetime import datetime, date
import plotly.graph_objects as go
from dotenv import load_dotenv
import dash_ag_grid as dag
import polars as pl
import numpy as np
import requests
import pyarrow
import json
import os

load_dotenv()
access_key = os.getenv("URA_ACCESS_KEY")
url = 'https://www.ura.gov.sg/uraDataService/insertNewToken.action'
headers = {
    'AccessKey': access_key,
    'User-Agent': 'curl/7.68.0'
}

token = requests.get(url, headers=headers).json().get("Result")
pp_url = f"https://www.ura.gov.sg/uraDataService/invokeUraDS?service=PMI_Resi_Transaction&batch="
pp_headers = {
    'AccessKey': access_key,
    'Token': token,
    'User-Agent': 'curl/7.68.0'
}

def fetch_data_for_period(period):
    response = requests.get(pp_url + period, headers=pp_headers)
    if response.status_code == 200:    
        return pl.DataFrame(response.json().get("Result"))
    else:
        return pl.DataFrame()  # Return empty DataFrame on error


# Use ThreadPoolExecutor to fetch data in parallel
# partitions = ['1', '2', '3', '4']
partitions = ['1', ]
df = pl.DataFrame()
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(
        fetch_data_for_period, period): period for period in partitions}

    for future in as_completed(futures):
        tmp = future.result()
        df = pl.concat([df, tmp], how="diagonal_relaxed")

print("Completed data extraction from URA")

final_df = df.clone()
final_df = (
    final_df
    .explode('transaction')
    .unnest("transaction")
    .drop("x", "y")
)

final_df = final_df.with_columns(
    pl.col("area").cast(pl.Decimal),
    pl.col("noOfUnits").cast(pl.Int16).alias("units"),
    pl.col("price").cast(pl.Decimal),
    pl.col('typeOfSale').cast(pl.Categorical).alias("sale_type"),
    pl.col('propertyType').alias("property"),
    pl.col('marketSegment').alias("region"),
    (pl.col("contractDate").str.slice(0, 2) + 
        "-20" + pl.col("contractDate").str.slice(-2)).alias("date"),
    pl.when(pl.col("nettPrice").is_null())
      .then(pl.col("price"))
      .otherwise(pl.col("nettPrice")).cast(pl.Decimal).alias("final_price")
)
final_df = final_df.with_columns(
        pl.col('final_price').alias('new_price'),
        pl.int_ranges("units").alias("list")
    ).explode('list').drop('list', "contractDate", "nettPrice", "price",
                           "final_price", "propertyType", "typeOfSale",
                           "marketSegment")

final_df = final_df.with_columns(
    (pl.col("new_price") / pl.col("units")).cast(pl.Float64).alias("final_price"),
    (pl.col("area") / pl.col("units")).cast(pl.Float64).alias("final_area")
)

final_df = final_df.with_columns(
   pl.when(pl.col("tenure") != "Freehold")
     .then(None)
     .otherwise(pl.col("tenure")) # keep original value
     .alias('freehold')
)

# Calculations for lease
final_df = final_df.with_columns(
    pl.col("tenure")
    .str.extract_all(r"\d+")
    .list.to_struct(fields=["lease", "lease_start"])
    .alias("lease_info")
).unnest("lease_info").with_columns(
    pl.col("lease").cast(pl.Decimal),
    pl.col("lease_start").cast(pl.Decimal)
).drop("noOfUnits", "new_price", "area")

# A set of calculations for lease_left
final_df = final_df.with_columns(
    pl.col("date").str.split("-")
    .list.to_struct(fields=["month", "year"])
    .alias("sold_date")
).unnest("sold_date").with_columns(
    ((pl.col("year").cast(pl.Float32)) - pl.col("lease_start")).alias("lease_used")
).with_columns((pl.col("lease") - pl.col("lease_used")).alias("lease_left")
).with_columns(
    # Fill lease of sales where freehold is null and no lease is defined yet
    (
        pl.when(
            (pl.col("freehold").is_null())
            & (pl.col("lease_start").is_null())
            & (pl.col('lease_left').is_null())
        )
        .then(99)
        .otherwise(pl.col("lease_left"))
    ).alias("final_lease_left")
)

# Calculate more price and area metircs
final_df = final_df.with_columns(
    (pl.col("final_price") / pl.col("final_area")).cast(pl.Float64).alias("price_sqm"),
    (pl.col("final_area") * 10.76391042).cast(pl.Float64).alias("final_area_sqft"),
).with_columns(
    (pl.col("final_price") / pl.col("final_area_sqft")).cast(pl.Float64).alias("price_sqft"),
    pl.col("date").str.to_date("%m-%Y"),
    pl.col("property").str.replace("Condominium", "Condo")
                      .replace("Strata", "S.")
                      .replace('Strata Semi-detached', "S. Semi-detached")
                      .replace('Strata Terrace', "S. Terrace")
                      .replace('Strata Detached', "S. Detached")
                      .replace("Executive Condo", "EC")
                      .replace("Semi-detached", "Semi-D")
).sort("date")

final_df = final_df.drop(
    'tenure', 'year', 'month', 'lease_left', 'units', 
    'sale_type').rename(
    {
        "floorRange": 'floor',
        "typeOfArea": "area_type",
        "final_lease_left": 'lease_left',
        'final_area_sqft': 'area_sqft',
        'final_price': 'price',
        'final_area': 'area_sqm'
    }
).with_columns(
    pl.col('price').round(2),
    pl.col('price_sqm').round(2),
    pl.col('price_sqft').round(2),
    pl.col('area_sqm').round(2),
    pl.col('area_sqft').round(2),
    pl.col("lease_left").cast(pl.String).fill_null(
        pl.col("freehold")).alias("freehold/lease")
)

cols_select = ['date', 'street', 'project', 'floor', 'district', 'region', # 'area_type',
               'property', 'freehold/lease',
               # 'freehold', 'lease_left',
               'price', 'price_sqm', 'price_sqft', 'area_sqft', 'area_sqm'] 

final_df = final_df.select(cols_select)

# Initalise App
app = Dash(
    __name__,
    external_stylesheets=[
        {'src': 'https://cdn.tailwindcss.com'},
        dbc.themes.BOOTSTRAP,
    ],
    requests_pathname_prefix="/private_housing/",
)

ag_table_cols = [
    {"field": 'date', "sortable": True},
    {"field": 'street', "sortable": True},
    {"field": 'project', "sortable": True},
    {"field": 'floor', "sortable": True},
    {"field": 'district', "sortable": True},
    # {"field": 'area_type', "sortable": True},
    {"field": 'property', "sortable": True},
    {"field": 'region', "sortable": True},
    # {"field": 'segment', "sortable": True},
    {"field": 'freehold/lease', "sortable": True},
    # {"field": 'final_lease', "sortable": True},
    {
        "field": 'price', "sortable": True,
        "valueFormatter": {"function": "d3.format('($,.2f')(params.value)"},

    },
    {
        "field": 'price_sqm', "sortable": True,
        "valueFormatter": {"function": "d3.format('($,.2f')(params.value)"},
    },
    {
        "field": 'price_sqft', "sortable": True,
        "valueFormatter": {"function": "d3.format('($,.2f')(params.value)"},
    },
    {
        "field": 'area_sqft', "sortable": True,
        "valueFormatter": {"function": "d3.format('(,.2f')(params.value)"},
    },
    {
        "field": 'area_sqm', "sortable": True,
        "valueFormatter": {"function": "d3.format('(,.2f')(params.value)"},
    },
]
chart_width, chart_height = 500, 450

app.layout = html.Div([
    # Text box to display dynamic content
    html.Div([
        html.Div([
            dcc.Loading([
                html.Div([
                    html.H3(
                        "Filtered Private Housing Transactions",
                        style={
                            "font-size": "15px",
                            "textAlign": "left",
                            "margin-top": "20px",
                        },
                    ),
                    dag.AgGrid(
                        id="price-table",
                        columnDefs=ag_table_cols,
                        rowData=final_df.select(cols_select).to_dicts(),
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

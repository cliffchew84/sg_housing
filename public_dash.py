#!/usr/bin/env python
# coding: utf-8

# HDB Dashboard Creation Workflow
import os
import json
import requests
import polars as pl
from datetime import datetime
from pymongo import mongo_client
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from concurrent.futures import ThreadPoolExecutor, as_completed


# MongoDB credentials
MONGO_PASSWORD = os.environ["mongo_pw"]
base_url = "mongodb+srv://cliffchew84:"
end_url = "cliff-nlb.t0whddv.mongodb.net/?retryWrites=true&w=majority"
mongo_url = f"{base_url}{MONGO_PASSWORD}@{end_url}"

# Update months in the latest year - Currently this is 2024
db = mongo_client.MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
db_nlb = db["nlb"]
df = pl.DataFrame(list(db_nlb["hdb_hist"].find({}, {"_id": 0})))

# Update months in the latest year - Currently this is 2024
current_date = datetime.today()
period_range = pl.date_range(
    datetime(year=2024, month=1, day=1), current_date, interval="1mo", eager=True
).to_list()
mths_2024 = [str(i)[:7] for i in period_range]

df_cols = ["month", "town", "resale_price"]
param_fields = ",".join(df_cols)
base_url = "https://data.gov.sg/api/action/datastore_search?resource_id="
ext_url = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"
full_url = base_url + ext_url

def fetch_hdb_data(period):
    params = {
        "fields": param_fields,
        "filters": json.dumps({"month": period}),
        "limit": 10000,
    }
    result = pl.DataFrame(schema=df_cols)
    response = requests.get(full_url, params=params)
    if response.status_code == 200:
        table_result = pl.DataFrame(response.json().get("result").get("records"))
        if table_result.columns != []:
            result = table_result
    return result


# Use ThreadPoolExecutor to fetch data in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(fetch_hdb_data, period): period for period in mths_2024}

    for future in as_completed(futures):
        mth_df = future.result()
        df = pl.concat([df, mth_df], how="vertical_relaxed")

# Data Processing for creating charts
bins = [300000, 500000, 800000, 1000000]
labels = ["0-300k", "300-500k", "500-800k", "800k-1m", ">=1m"]

df = (
    df.filter("month" >= "2020-01-01")
    .with_columns(pl.lit(1).alias("count"), 
                  pl.col("resale_price").cast(pl.Float64))
    .rename({"resale_price": "price"})
    .with_columns(
        pl.col("price")
        .cut(breaks=bins, labels=labels, left_closed=True)
        .alias("price_grp")
    )
)

price_grps = df["price_grp"].unique().to_list()
price_grps.sort()

price_grps_dict = dict()
price_grps_dict[price_grps[0]] = "#8BC1F7"
price_grps_dict[price_grps[1]] = "#06C"
price_grps_dict[price_grps[2]] = "#4CB140"
price_grps_dict[price_grps[3]] = "#F0AB00"
price_grps_dict[price_grps[4]] = "#C9190B"

chart_width, chart_height = 1000, 600
legend = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
period_list = (
    df.select(pl.col("month")).unique(maintain_order=True).to_series().to_list()
)
today = str(datetime.today().date())
note = f"Updated on {today}"


# Home price distributions
def create_home_price_dist(df=df, note=note):
    p_count = df.group_by("month").agg(pl.col("price").median())
    p_count = p_count.with_columns(
        pl.when(pl.col("price") >= 500000).then(1).otherwise(0).alias("price_bar")
    )

    high_prices = (
        p_count.filter(pl.col("price_bar") == 1).select("month").to_series().to_list()
    )
    low_prices = (
        p_count.filter(pl.col("price_bar") == 0).select("month").to_series().to_list()
    )

    fig = go.Figure()
    for p in period_list:
        tmp = df.filter(pl.col("month") == p)
        if p in high_prices:
            fig.add_trace(
                go.Box(
                    y=tmp.select("price").to_series(),
                    name=str(p),
                    boxpoints="outliers",
                    marker_color="#C9190B",
                    line_color="#C9190B",
                    showlegend=False,
                )
            )
        else:
            fig.add_trace(
                go.Box(
                    y=tmp.select("price").to_series(),
                    name=str(p),
                    boxpoints="outliers",
                    marker_color="#06C",
                    line_color="#06C",
                    showlegend=False,
                )
            )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            name="Median Price <500K",
            marker=dict(size=7, color="#06C", symbol="circle"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            name="Median Price > 500K",
            marker=dict(size=7, color="#C9190B", symbol="circle"),
        )
    )

    fig.update_layout(
        title="Public Home Price Distributions",
        yaxis={"title": "Prices (SGD)"},
        xaxis={"title": "Months"},
        width=chart_width,
        height=chart_height,
        legend=legend,
    )
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


# Advanced Million Dollar Homes
def create_mil_bar_chart(df=df, note=note):
    mil = (
        df.with_columns(
            pl.when(pl.col("price") >= 1000000).then(1).otherwise(0).alias("mil")
        )
        .group_by(["month", "mil"])
        .agg(pl.col("town").count())
        .sort("month")
        .pivot(on="mil", index="month", values="town", aggregate_function="sum")
        .fill_null(0)
        .with_columns((pl.col("1") + pl.col("0")).alias("All"))
        .with_columns(((pl.col("1") / pl.col("All")) * 100).round(2).alias("prop"))
        .rename(
            {"1": "million $ Trans", "All": "Total Trans", "prop": "% million Trans"}
        )
    )

    title = f"% of Million Dollar Homes & Total Homes Sold<br>{note}"

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=mil.select("month").to_series().to_list(),
            y=mil.select("% million Trans").to_series().to_list(),
            mode="lines+markers",
            name="%",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=mil.select("month").to_series().to_list(),
            y=mil.select("Total Trans").to_series().to_list(),
            opacity=0.4,
            name="Total Sales",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title=title,
        hovermode="x unified",
        xaxis={"title": "Months"},
        width=chart_width,
        height=chart_height,
        legend=legend,
    )

    fig.update_yaxes(
        title_text="Million Dollar Homes / Total Home Sales (%)", secondary_y=False
    )
    fig.update_yaxes(title_text="Total Sales", secondary_y=True)

    fig.add_hline(y=1, line_width=1.5, line_dash="dash", line_color="black")
    fig.add_hline(y=3, line_width=1.5, line_dash="dash", line_color="purple")
    fig.add_hline(y=4, line_width=1.5, line_dash="dash", line_color="red")
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


# Stacked Bar Values
def create_price_grp_counts(df=df, note=note):
    pg_plots = df.group_by(["month", "price_grp"]).agg(pl.col("count").sum())

    fig = go.Figure()
    for i in price_grps:
        fig.add_trace(
            go.Bar(
                name=i,
                x=pg_plots.filter(pl.col("price_grp") == i)
                .select("month")
                .to_series()
                .to_list(),
                y=pg_plots.filter(pl.col("price_grp") == i)
                .select("count")
                .to_series()
                .to_list(),
                marker_color=price_grps_dict[i],
            )
        )

    fig.update_layout(
        barmode="stack",
        xaxis={"title": "Months"},
        yaxis={"title": "Count"},
        hovermode="x unified",
        title=f"Total Public Home Sales by Price Category<br>{note}",
        width=chart_width,
        height=chart_height,
        legend=legend,
    )
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def create_price_grp_percent(df=df, note=note):
    pg_base = df.group_by("month").agg(pl.col("count").sum())
    pg_plots = df.group_by(["month", "price_grp"]).agg(pl.col("count").sum())
    for_plots = pg_plots.join(pg_base, on="month")

    for_plots.columns = ["month", "price_grp", "count", "total"]
    for_plots = for_plots.with_columns(
        (100 * pl.col("count") / pl.col("total")).round(1).alias("percent_count")
    )

    fig = go.Figure()
    for i in price_grps:
        fig.add_trace(
            go.Bar(
                name=i,
                x=for_plots.filter(pl.col("price_grp") == i)
                .select("month")
                .to_series()
                .to_list(),
                y=for_plots.filter(pl.col("price_grp") == i)
                .select("percent_count")
                .to_series()
                .to_list(),
                marker_color=price_grps_dict[i],
            )
        )

    fig.add_hline(y=50, line_width=1.5, line_dash="dash", line_color="black")
    fig.update_layout(
        barmode="stack",
        title=f"% of Public Home Sales by Price Category<br>{note}",
        xaxis={"title": "Months"},
        yaxis={"title": "%"},
        hovermode="x unified",
        width=chart_width,
        height=chart_height,
        legend=legend,
    )
    return fig.to_html(full_html=False, include_plotlyjs="cdn")

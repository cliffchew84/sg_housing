import geopy.distance
import polars as pl
import numpy as np


def create_mdb_query_w_df_cols(df: pl.DataFrame):
    """
    Creates mongoDB query from dataframe,
    list or string of known column names
    """

    if type(df) is pl.DataFrame:
        col_names = df.columns
    elif type(df) is list:
        col_names = df
    elif type(df) is str:
        col_names = [i.strip() for i in df.split(',')]

    col_dict = dict()
    col_filter = {"_id": 0}

    for name in col_names:
        col_dict[name] = {"$exists": True}
        col_filter[name] = 1

    return col_dict, col_filter


def table_select_from_pt(df: pl.DataFrame,
                         loc_ll: tuple,
                         select=True,
                         radius=1000) -> pl.DataFrame:
    """ Takes a Tuple Lat-Long input, a set of tables with Lat-Longs,
    and filters for records that are included or excluded by a radius
    distance
    """
    
    # TODO - Fix to fully polars dataframe 
    df_lat = df[.select('LATITUDE').to_series().to_list()
    df_long = df.select('LONGITUDE').to_series().to_list()

    df['dist'] = [geopy.distance.geodesic(
        (float(i), float(j)), loc_ll).m for i, j in zip(df_lat, df_long)]

    if select:
        selected_df = df[df['dist'] <= radius].reset_index(drop=True)
    else:
        selected_df = df[df['dist'] > radius].reset_index(drop=True)

    return selected_df

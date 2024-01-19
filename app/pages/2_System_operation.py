import streamlit as st
st.set_page_config(
    layout="wide"
)

import os
import pathlib
import pages.utils.system_operation_prerun as helper
import pages.utils.tools as tools

import pandas as pd
import pypsa
import numpy as np
import plotly.express as px
import re
import xarray as xr
import geopandas as gpd
import plotly.graph_objects as go
import shapely.geometry
import math
import yaml
import hvplot.pandas
import holoviews as hv
from bokeh.models import HoverTool  
from bokeh.plotting import figure, show
from holoviews import Store
import networkx as nx
import hvplot.networkx as hvnx
from shapely.geometry import Point, LineString, shape
import datetime

# needed to change cursor mode of selectboxes from the default text mode
fix_cursor_css = '''
    <style>
        .stSelectbox:first-of-type > div[data-baseweb="select"] > div {
            cursor: pointer;      
        }            
    </style>
'''

non_empth_links_keys = [param for param in helper.config["links_t_parameter"]]
non_empth_loads_keys = [param for param in helper.config["loads_t_parameter"]]

# TODO avarage by carriers
# detailed by carrier and countries
gen_dict_list = helper.get_gen_t_dict()
#storage_df = helper.get_storage_t_dict()
loads_dict_list = helper.get_load_t_dict()
#stores_df = helper.get_components_t_dict("stores_t", non_empth_stores_keys)

res_choices = helper.config["operation"]["resolution"]

kwargs = dict(
        stacked=False,
        line_width=0,
        xlabel="",
        width=800,
        height=550,
        hover=False,
        legend="right",
        alpha=0.8
    )
plot_font_dict = dict(
    title=18,
    legend=18,
    labels=18, 
    xticks=18, 
    yticks=18,
)

st.title("System operation")

_, main_col, _, suppl_col, _ = st.columns([1, 35, 1, 20, 1])

def scenario_formatter(scenario):
    return helper.config["scenario_names"][scenario]

def get_carrier_map():
    return helper.config["carrier"]

def get_colors_map():
    return helper.config["tech_colors"]  

carriers_map = get_carrier_map()
tech_map = dict(map(reversed, carriers_map.items()))
tech_colors = get_colors_map()

tools.add_logo()
with main_col:
    selected_network = st.selectbox(
        "Select which scenario's plot you want to see :",
        list(gen_dict_list.keys()),
        format_func = scenario_formatter,
        help="You can choose between available scenarios"
    )
    st.markdown(fix_cursor_css, unsafe_allow_html=True)

# the finest available resolution depends on the model and should be extracted from metadata
# https://stackoverflow.com/a/9891784/8465924    
pat = r".*?\-(.\d)H.*"
sector_scen_string = helper.get_meta_df(selected_network)["scenario"]["sector_opts"]
finest_resolution = re.search(pat, sector_scen_string[0]).group(1)    
finest_resolution_name = finest_resolution.split("H")[0] + "-hourly"
upd_dict = {finest_resolution: finest_resolution_name}
upd_dict.update(res_choices)

with suppl_col:
    choices = upd_dict
    res = st.selectbox(
        "Resolution",
        choices,
        format_func=lambda x: choices[x], 
        key="gen_res",
        help="You can choose a resolution for time aggregation applied for a plot"
    )
    st.markdown(fix_cursor_css, unsafe_allow_html=True) 

country_data = gen_dict_list.get(selected_network)

##################### generators #####################
gen_df = country_data["p"].drop("Load", axis=1, errors="ignore")

_, date_range_param, _ = st.columns([1, 50, 1])
with date_range_param:
    min_index = gen_df.index[0]
    max_index = gen_df.index[-1]
    min_value = datetime.datetime(min_index.year, min_index.month, min_index.day)
    max_value = datetime.datetime(max_index.year, max_index.month, max_index.day)
    values = st.slider(
            "Select a range of values",
            min_value, max_value, (min_value, max_value),
            # step=datetime.timedelta(hours=int(res[:-1])),
            format="D MMM, HH:mm",
            label_visibility="hidden",
            key="gen_date"
        )

###################### demand #####################
loads_country_data=loads_dict_list.get(selected_network)
#stores_country_data=stores_df.get(selected_network)

loads_df = loads_country_data["p"]
heat_loads_df = loads_df.filter(like="heat")
#heat_loads_df = loads_df.filter(like="Heating")

###################### generation #####################

# TODO wouldn't it be more reliabe to move columns renaming there?
#gen_df.columns = [tech_map[c] for c in gen_df.columns]

#TODO Add balance?
balance_df = gen_df

# TODO Check if res contains only numbers
res_h = str(res) + "H"

balance_aggr = balance_df.loc[values[0]:values[1]].resample(res_h).mean()
heat_aggr = heat_loads_df.loc[values[0]:values[1]].resample(res_h).mean()

heat_aggr["Overall"] = heat_aggr.sum(axis=1)
# TODO make filtering case insensitive/based on regex
heat_aggr["Overall Flatten"] = heat_aggr["Overall"] - balance_aggr.filter(like="etrofi").filter(like="oder").sum(axis=1)

#res_heat = balance_aggr
#res_heat["Overall"] = heat_aggr.sum(axis=1)
#res_heat["Overall Flatten"] = res_heat["Overall"] - balance_aggr.filter(like="etrofi").filter(like="oder").sum(axis=1)

_, balance_plot_col, _ = st.columns([1, 80, 1])

with balance_plot_col:
    #heat_dem_area_plot=res_heat.filter(like="eat").hvplot.area(
    heat_dem_area_plot=heat_aggr[["Overall", "Overall Flatten"]].hvplot.area(         
         **kwargs,
         ylabel="Heat Demand [MW]",
         group_label=helper.config["loads_t_parameter"]["p"]["legend_title"],
         color = ["#ffc100", "#ff9a00", "#ff7400", "#ff4d00", "#ff0000"]
         )
    heat_dem_line_plot=heat_aggr[["Overall", "Overall Flatten"]].hvplot.line(
         color = ["#333333", "#777777",]
     )
    heat_dem_area_plot = heat_dem_area_plot.opts(
         fontsize=plot_font_dict
     )         
    s2=hv.render(heat_dem_area_plot*heat_dem_line_plot, backend="bokeh")
    st.bokeh_chart(s2, use_container_width=True)

tools.add_logo()  

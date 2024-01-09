import streamlit as st
st.set_page_config(
    layout="wide"
)

import os
import pathlib
import app.pages.utils.system_operation_prerun as helper
import app.pages.utils.tools as tools

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
non_empth_stores_keys = [param for param in helper.config["stores_t_parameter"]]

# average by carrier
gen_dict_list = helper.get_gen_t_dict()
#storage_df = helper.get_storage_t_dict()
loads_dict_list = helper.get_load_t_dict()
#stores_df = helper.get_components_t_dict("stores_t", non_empth_stores_keys)

# carrier values per bus
gen_buses_dict_list = helper.get_buses_gen_t_dict()
load_buses_dict_list = helper.get_buses_load_t_dict()

res_choices = helper.config["operation"]["resolution"]

kwargs = dict(
        stacked=True,
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

# TODO naming should be imroved
country_data = gen_dict_list.get(selected_network)
buses_country_data = gen_buses_dict_list.get(selected_network)
buses_load_country_data = load_buses_dict_list.get(selected_network)

##################### generators #####################
gen_df = country_data["p"].drop("Load", axis=1, errors="ignore")
# TODO naming should be imroved: gen_buses_df can be distinguished 
# between the dataframe and the dictionary
gen_buses_df = buses_country_data["p"].drop("Load", axis=1, errors="ignore")
load_buses_df = buses_load_country_data["p"]

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
heat_loads_df = loads_df.filter(like="Heating")

###################### generation #####################

# ensure consistency of columns naming for generation and demand
#gen_df.columns = [tech_map[c] for c in gen_df.columns]

balance_df = gen_df

# TODO Check if res contains only numbers
res_h = str(res) + "H"
balance_aggr = balance_df.loc[values[0]:values[1]].resample(res_h).mean()
heat_aggr = heat_loads_df.loc[values[0]:values[1]].resample(res_h).mean()

heat_aggr["Overall"] = heat_aggr.sum(axis=1)
# TODO make filtering case insensitive/based on regex
heat_aggr["Overall Flatten"] = heat_aggr["Overall"] - balance_aggr.filter(like="etrofi").filter(like="oder").sum(axis=1)

_, balance_plot_col, _ = st.columns([1, 80, 1])

with balance_plot_col:
     heat_dem_area_plot=heat_aggr.filter(like="eat").hvplot.area(
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

# plot by buses --------------------------------------

gen_buses_aggr = gen_buses_df.loc[values[0]:values[1]].resample(res_h).mean()
load_buses_aggr = load_buses_df.loc[values[0]:values[1]].resample(res_h).mean()

country_code = "PL"

gen_buses_aggr = gen_buses_aggr.filter(like=country_code)
load_buses_aggr = load_buses_aggr.filter(like=country_code)


with balanse_plot_col:
    buses_gen_area_plot = load_buses_aggr.filter(like="Heating").hvplot.area(
        **kwargs,
        ylabel="Supply [MW]",
        #group_label=helper.config["loads_t_parameter"]["p"]["legend_title"],
        color = ["#ffc100", "#ff9a00", "#ff7400", "#ff4d00", "#ff0000"]
        )
    buses_gen_area_plot = buses_gen_area_plot.opts(
        fontsize=plot_font_dict
    )         
    s2=hv.render(buses_gen_area_plot, backend="bokeh")
    st.bokeh_chart(s2, use_container_width=True)    






with balanse_plot_col:
    heat_dem_area_plot=heat_aggr.hvplot.area(
        **kwargs,
        ylabel="Heat Demand [MW]",
        group_label=helper.config["loads_t_parameter"]["p"]["legend_title"],
        #color = plot_color
        )
    heat_dem_area_plot = heat_dem_area_plot.opts(
        fontsize=plot_font_dict
    )         
    s2=hv.render(heat_dem_area_plot, backend="bokeh")
    st.bokeh_chart(s2, use_container_width=True)

with balanse_plot_col:
    heat_smooth_area_plot=heat_smoothed_aggr[["Overall Heating Retrofitted", "Overall Heating"]].hvplot.area(
        **kwargs,
        ylabel="Retrofitting Effect on Heat Demand [MW]",
        group_label=helper.config["loads_t_parameter"]["p"]["legend_title"],
        #color = plot_color
        )
    heat_smooth_area_plot = heat_smooth_area_plot.opts(
        fontsize=plot_font_dict
    )         
    s2=hv.render(heat_smooth_area_plot, backend="bokeh")
    st.bokeh_chart(s2, use_container_width=True)


with balanse_plot_col:
    #balanse_area_plot=balance_aggr[retrofit_ambitious_cols].hvplot.area(
        #color = ["coral"]
    #balanse_area_plot=balance_aggr[["solar", "onwind"]].hvplot.area(
    #    color = ["green", "blue"]
    #)
    balanse_area_plot = balance_aggr[retrofit_moderate_cols].hvplot.area(
        **kwargs,
        ylabel="Retrofitting in action [MW]",
        group_label=helper.config["loads_t_parameter"]["p"]["legend_title"],
        #color = plot_color
        )
    balanse_area_plot = balanse_area_plot.opts(
        fontsize=plot_font_dict
    )         
    s2=hv.render(balanse_area_plot, backend="bokeh")
    st.bokeh_chart(s2, use_container_width=True)

tools.add_logo()  

###################### supply-demand balanse #####################

# ensure consistency of columns naming for generation and demand
#gen_df.columns = [tech_map[c] for c in gen_df.columns]

balance_df = gen_df

#balance_df = (
#    pd.concat([gen_df, demand_df], axis=1)
#    .drop("battery", axis=1)
#    .drop("H2", axis=1)
#    .drop("nH2", axis=1)
#    .drop("load", axis=1)
#)

#dem_balance_df = (
#    demand_df
#    .drop("battery", axis=1)
#    .drop("H2", axis=1)
#    .drop("pH2", axis=1)
#)
#
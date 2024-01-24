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

warm_orange_pallette = ["#ffe289", "#ffd966", "#ffc100", "#ff9a00", "#ff7400", 
    "#ff4d00", "#ff0000", "#d60000", "#b20000", "#8e0000"]

non_empth_links_keys = [param for param in helper.config["links_t_parameter"]]
non_empth_loads_keys = [param for param in helper.config["loads_t_parameter"]]
non_empth_links_keys = [param for param in helper.config["links_t_parameter"]]

# carrier values per bus
gen_buses_dict_list = helper.get_buses_gen_t_dict()
load_buses_dict_list = helper.get_buses_load_t_dict()
links_buses_dict_list = helper.get_buses_links_t_dict()

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
    title=14,
    legend=14,
    labels=14, 
    xticks=14, 
    yticks=14,
)

st.title("Country operation")

_, main_col, _, country_col, _, date_col, _ = st.columns([1, 35, 1, 20, 1, 20, 1])

def scenario_formatter(scenario):
    return helper.config["scenario_names"][scenario]

def country_formatter(country_code):
    return helper.config["countries_names"][country_code]

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
        list(gen_buses_dict_list.keys()),
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

with date_col:
    choices = upd_dict
    res = st.selectbox(
        "Resolution",
        choices,
        format_func=lambda x: choices[x], 
        key="gen_res",
        help="You can choose a resolution for time aggregation applied for a plot"
    )
    st.markdown(fix_cursor_css, unsafe_allow_html=True) 

# # TODO naming should be imroved
# country_data = gen_dict_list.get(selected_network)
buses_country_data = gen_buses_dict_list.get(selected_network)
buses_load_country_data = load_buses_dict_list.get(selected_network)
buses_links_country_data = links_buses_dict_list.get(selected_network)

##################### generators #####################
# gen_df = country_data["p"].drop("Load", axis=1, errors="ignore")
# TODO naming should be imroved: gen_buses_df can be distinguished 
# between the dataframe and the dictionary
gen_buses_df = buses_country_data["p"].drop("Load", axis=1, errors="ignore")
load_buses_df = buses_load_country_data["p"]
cons_links_df = buses_links_country_data["p0"]

countries_codes = pd.unique(
    [(lambda x: re.sub("\d.*", '', x))(x) for x in gen_buses_df.columns]
)
# to avoid mis-interpretaiton of regex outputs
country_codes_clean = [x for x in countries_codes if x in helper.config["countries_names"].keys()]
country_codes_clean = sorted(country_codes_clean)
with country_col:
    ctr = st.selectbox(
        "Country",
        country_codes_clean,
        format_func=country_formatter, 
        key="country",
        help="You can choose a country to examine operation of the energy system"
    )
    st.markdown(fix_cursor_css, unsafe_allow_html=True)  

_, date_range_param, _ = st.columns([1, 50, 1])
with date_range_param:
    min_index = gen_buses_df.index[0]
    max_index = gen_buses_df.index[-1]
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

# ###################### time aggregation #####################

# # TODO wouldn't it be more reliabe to move columns renaming there?
# #gen_df.columns = [tech_map[c] for c in gen_df.columns]

# #TODO Add balance?
# balance_df = gen_df

if res.isdigit():
    res = str(res) + "H"

_, balance_plot_col, _ = st.columns([1, 80, 1])

gen_buses_aggr = gen_buses_df.loc[values[0]:values[1]].resample(res).mean()
load_buses_aggr = load_buses_df.loc[values[0]:values[1]].resample(res).mean()
cons_links_aggr = cons_links_df.loc[values[0]:values[1]].resample(res).mean()

# ###################### space heating #####################

gen_buses_retrof_aggr = gen_buses_aggr.filter(like=ctr).filter(like="retrof")
gen_buses_retrof_aggr.columns.name = None

load_buses_heat_aggr = load_buses_aggr.filter(like=ctr).filter(like="heat")
load_buses_space_heat_aggr = load_buses_heat_aggr.loc[:,~load_buses_heat_aggr.columns.str.endswith("industry")]
load_buses_space_heat_aggr.columns.name = None
load_buses_space_heat_aggr["space heating original"] = load_buses_space_heat_aggr.sum(axis=1)
load_buses_space_heat_aggr["space heating overall"] = load_buses_space_heat_aggr["space heating original"] - gen_buses_retrof_aggr.sum(axis=1)

heat_techs = ["residential rural heat", "residential urban decentral heat",
              "services rural heat", "services urban decentral heat",
              "urban central heat"]

with balance_plot_col:
    buses_heat_area_plot = load_buses_space_heat_aggr[load_buses_space_heat_aggr.columns.difference(["space heating overall", "space heating original"])].hvplot.area(
        **kwargs,
        ylabel="Heat Demand [MW]",
        group_label=helper.config["loads_t_parameter"]["p"]["legend_title"],
        color = [tech_colors[x] for x in heat_techs]
        )
    buses_heat_area_plot = buses_heat_area_plot.opts(
        fontsize=plot_font_dict
    )
    buses_ovheat_line_plot = (
        load_buses_space_heat_aggr["space heating overall"].hvplot
        .line(color=[tech_colors[x] for x in ["space heating overall"]])
    )
    buses_orheat_line_plot = (
        load_buses_space_heat_aggr["space heating original"].hvplot
        .line(color=[tech_colors[x] for x in ["space heating original"]])
    )
    buses_heat_area_plot = buses_heat_area_plot * buses_ovheat_line_plot
    buses_heat_area_plot = buses_heat_area_plot * buses_orheat_line_plot           
    s2=hv.render(buses_heat_area_plot, backend="bokeh")
    st.bokeh_chart(s2, use_container_width=True)

if gen_buses_retrof_aggr.sum().sum()>0:
    with balance_plot_col:
        buses_retrof_area_plot = gen_buses_retrof_aggr.hvplot.area(
            **kwargs,
            ylabel="Retrofitting [MW]",
            group_label=helper.config["loads_t_parameter"]["p"]["legend_title"],
            color = warm_orange_pallette
            )
        buses_retrof_area_plot = buses_retrof_area_plot.opts(
            fontsize=plot_font_dict
        )
        # buses_ovheat_line_plot = load_buses_space_heat_aggr["space heating overall"].hvplot.line(color="navy")
        # buses_orheat_line_plot = load_buses_space_heat_aggr["space heating original"].hvplot.line(color="darkred")
        # buses_retrof_area_plot = buses_retrof_area_plot * buses_ovheat_line_plot
        # buses_retrof_area_plot = buses_retrof_area_plot * buses_orheat_line_plot           
        s2=hv.render(buses_retrof_area_plot, backend="bokeh")
        st.bokeh_chart(s2, use_container_width=True)    

# ###################### electricity load #####################

# keep only columns like "AL1 0"
power_cols = [x for x in load_buses_aggr.columns if re.match("^[0-9 ]+$", re.sub(ctr, "", x))]
load_el_buses_aggr = load_buses_aggr[power_cols]
load_el_buses_aggr.columns.name = None
load_el_buses_aggr.index = pd.to_datetime(load_el_buses_aggr.index)

#cons_hp_links_aggr = cons_links_aggr.filter(like=ctr).filter(like="heat pump")
regional_cons_links_aggr = cons_links_aggr.filter(like=ctr).filter(like=ctr)
# cols_of_interest = regional_cons_links_aggr.columns.str.contains("resistive heater|H2 Electrolysis|heat pump")
cols_of_interest = regional_cons_links_aggr.columns.str.contains("resistive heater|heat pump")
cons_hp_links_aggr = regional_cons_links_aggr[regional_cons_links_aggr.columns[cols_of_interest]]
cons_hp_links_aggr.index = pd.to_datetime(cons_hp_links_aggr.index)

regional_load_buses_aggr = load_buses_aggr.filter(like=ctr)
regional_load_buses_aggr.columns.name = None
regional_load_buses_aggr.index = pd.to_datetime(regional_load_buses_aggr.index)

heat_el_buses_aggr = pd.concat(
    [cons_hp_links_aggr, regional_load_buses_aggr.filter(like="industry electricity")],
    axis = 1
)    
heat_el_buses_aggr["power"] = load_el_buses_aggr.sum(axis=1)

with balance_plot_col:
    buses_el_area_plot = heat_el_buses_aggr[heat_el_buses_aggr.columns.difference(["power"])].hvplot.area(
        **kwargs,
        ylabel="Electricity Consumption [MW]",
        group_label=helper.config["links_t_parameter"]["p0"]["legend_title"],
        color = warm_orange_pallette
        )
    buses_el_line_plot = heat_el_buses_aggr["power"].hvplot.line(color="#8B0000")
    buses_el_area_plot = buses_el_area_plot * buses_el_line_plot
    buses_el_area_plot = buses_el_area_plot.opts(
        fontsize=plot_font_dict
    )         
    s2=hv.render(buses_el_area_plot, backend="bokeh")
    st.bokeh_chart(s2, use_container_width=True)

tools.add_logo()  
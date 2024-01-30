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

# TODO Replace by the proper colors definition
warm_orange_pallette = ["#ffe289", "#ffd966", "#ffc100", "#ff9a00", "#ff7400", 
    "#ff4d00", "#ff0000", "#d60000", "#b20000", "#8e0000"]

non_empth_links_keys = [param for param in helper.config["links_t_parameter"]]
non_empth_loads_keys = [param for param in helper.config["loads_t_parameter"]]
non_empth_links_keys = [param for param in helper.config["links_t_parameter"]]

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

_, scen_col, _, country_col, _, date_col, _ = st.columns([1, 35, 1, 20, 1, 20, 1])

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

#country_codes_clean = helper.config["countries_names"].keys()
country_dict = dict(sorted(helper.config["countries_names"].items(), key=lambda item: item[1]))
country_dict_clean = {"all": country_dict.pop("all"), **country_dict}
country_codes_clean = country_dict_clean.keys()
with country_col:
    ctr = st.selectbox(
        "Country",
        country_codes_clean,
        format_func=country_formatter, 
        key="country",
        help="You can choose a country to examine operation of the energy system"
    )
    st.markdown(fix_cursor_css, unsafe_allow_html=True)

# extract dataframes from all the available networks
gen_buses_dict_list = helper.get_buses_gen_t_dict(ctr)
load_buses_dict_list = helper.get_buses_load_t_dict(ctr)
links_buses_dict_list = helper.get_buses_links_t_dict(ctr)

with scen_col:
    selected_network = st.selectbox(
        "Select which scenario's plot you want to see :",
        list(gen_buses_dict_list.keys()),
        format_func = scenario_formatter,
        help="You can choose between available scenarios"
    )
    st.markdown(fix_cursor_css, unsafe_allow_html=True) 

buses_country_data = gen_buses_dict_list.get(selected_network)
gen_buses_df = buses_country_data["p"].drop("Load", axis=1, errors="ignore")

buses_load_country_data = load_buses_dict_list.get(selected_network)
load_buses_df = buses_load_country_data["p_set"]

buses_links_country_data = links_buses_dict_list.get(selected_network)
cons_links_df = buses_links_country_data["p0"]
cons_links_df1 = buses_links_country_data["p1"]
cons_links_df2 = buses_links_country_data["p2"]
cons_links_df3 = buses_links_country_data["p3"]

# metadata for time resolution may be wrong; keeping the meta-data approach for reference only
# the finest available resolution depends on the model and should be extracted from metadata
# https://stackoverflow.com/a/9891784/8465924    
#pat = r".*?\-(.\d)H.*"
#sector_scen_string = helper.get_meta_df(selected_network)["scenario"]["sector_opts"]
#finest_resolution = re.search(pat, sector_scen_string[0]).group(1)    
#finest_resolution_name = finest_resolution.split("H")[0] + "-hourly"
finest_resolution = round(((gen_buses_df.index[1] - gen_buses_df.index[0]).seconds)/3600)
finest_resolution_name = str(finest_resolution) + "-hourly"
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
    
if str(res).isdigit():
    res = str(res) + "H"

_, balance_plot_col, _ = st.columns([1, 80, 1])

gen_buses_aggr = gen_buses_df.loc[values[0]:values[1]].resample(res).mean()
load_buses_aggr = load_buses_df.loc[values[0]:values[1]].resample(res).mean()
cons_links_aggr = cons_links_df.loc[values[0]:values[1]].resample(res).mean()
cons_links_aggr1 = cons_links_df1.loc[values[0]:values[1]].resample(res).mean()
cons_links_aggr2 = cons_links_df2.loc[values[0]:values[1]].resample(res).mean()
cons_links_aggr3 = cons_links_df3.loc[values[0]:values[1]].resample(res).mean()

# ###################### space heating #####################

load_buses_aggr["Heating Original"] = load_buses_aggr.filter(like="Heating").sum(axis=1)
load_buses_aggr["Heating Retrof"] = load_buses_aggr["Heating Original"] - gen_buses_aggr.filter(like="Retrofitting").sum(axis=1)


#cols_df = pd.DataFrame(
#    {
#        "heating_col": ["Urb Centr Heating", "Urb Decentr Heating", "Rural Decentr Heating"],
#        "retrofitting_col": ["Retrofitting Urban Central", "Retrofitting Urban Decentral", "Retrofitting Rural"],
#        "retrofitting_col_nn": ["Urb Centr Heating Retrof", "Urb Decentr Heating Retrof", "Rural Heating Retrof"]
#    }
#)
#for i in [0, 1, 2]:
#    if cols_df.loc[i, "heating_col"] in load_buses_aggr.columns:
#        load_buses_aggr[cols_df.loc[1, "retrofitting_col_nn"]] = load_buses_aggr[cols_df.loc[1, "heating_col"]] - gen_buses_aggr[cols_df.loc[1, "retrofitting_col"]]


if "Urb Centr Heating" in load_buses_aggr.columns:
    load_buses_aggr["Urb Centr Heating Retrof"] = load_buses_aggr["Urb Centr Heating"] - gen_buses_aggr["Retrofitting Urban Central"]
if "Urb Decentr Heating" in load_buses_aggr.columns:    
    load_buses_aggr["Urb Decentr Heating Retrof"] = load_buses_aggr["Urb Decentr Heating"] - gen_buses_aggr["Retrofitting Urban Decentral"]
if "Rural Decentr Heating" in load_buses_aggr.columns:
    load_buses_aggr["Rural Heating Retrof"] = load_buses_aggr["Rural Decentr Heating"] - gen_buses_aggr["Retrofitting Rural"]

heat_techs = ["residential rural heat", "residential urban decentral heat",
              "services rural heat", "services urban decentral heat",
              "urban central heat"]

heat_cols_to_plot = ["Rural Heating Retrof", "Urb Decentr Heating Retrof", 
                "Urb Centr Heating Retrof"]

cols_to_plot = pd.Index(
    pd.Index(heat_cols_to_plot)
    .intersection(load_buses_aggr.columns)
    #.append(heat_supply_buses_aggr.columns.difference(heat_cols_to_plot))
)

with balance_plot_col:
    buses_heat_area_plot = load_buses_aggr[cols_to_plot].hvplot.area(
        **kwargs,
        ylabel="Heat Demand [MW]",
        group_label=helper.config["loads_t_parameter"]["p_set"]["legend_title"],
        color = [tech_colors[x] for x in cols_to_plot]
        )
    buses_ovheat_line_plot = (
        load_buses_aggr["Heating Retrof"].hvplot
        .line(color=[tech_colors[x] for x in ["space heating overall"]])
    )
    buses_orheat_line_plot = (
        load_buses_aggr["Heating Original"].hvplot
        .line(color=[tech_colors[x] for x in ["space heating original"]])
    )
    buses_heat_area_plot = buses_heat_area_plot * buses_ovheat_line_plot
    buses_heat_area_plot = buses_heat_area_plot * buses_orheat_line_plot 
    buses_heat_area_plot = buses_heat_area_plot.opts(
        ylim=(0, None),
        active_tools=[],
        fontsize=plot_font_dict
    )         
    s2=hv.render(buses_heat_area_plot, backend="bokeh")
    st.bokeh_chart(s2, use_container_width=True)

if gen_buses_aggr.filter(like="Retrofitting").sum(axis=1).sum()>0:

    cols_to_plot = ["Retrofitting Rural", 
                    "Retrofitting Urban Decentral", "Retrofitting Urban Central"]
     
    with balance_plot_col:
        buses_retrof_area_plot = gen_buses_aggr[cols_to_plot].hvplot.area(
            **kwargs,
            ylabel="Retrofitting [MW]",
            group_label=helper.config["loads_t_parameter"]["p_set"]["legend_title"],
            color = [tech_colors[x] for x in cols_to_plot]
            )
        buses_retrof_area_plot = buses_retrof_area_plot.opts(
            ylim=(0, None),            
            active_tools=[],
            fontsize=plot_font_dict
        )           
        s2=hv.render(buses_retrof_area_plot, backend="bokeh")
        st.bokeh_chart(s2, use_container_width=True)

# ###################### heat supply #####################

heat_supply_cols = cons_links_aggr1.columns[cons_links_aggr1.columns.isin(
    ["Air Heat Pump", "Ground Heat Pump",
     #"Biomass CHP", "Gas CHP", "Microgas CHP",
     #"H2 Fuel Cell",
    "Biomass Boiler", "Gas Boiler", 
    "Resistive Heater"]
)]

heat_supply_buses_aggr = -cons_links_aggr1[heat_supply_cols]
heat_supply_buses_aggr["TES"] = -cons_links_aggr1.filter(like="water tanks discharger").sum(axis=1)

heat_supply_buses_aggr["CHP"] = -cons_links_aggr2.filter(like="CHP").sum(axis=1)
heat_supply_buses_aggr["Fuel Cell"] = -cons_links_aggr2.filter(like="Fuel Cell").sum(axis=1)

heat_supply_buses_aggr["Fischer-Tropsch"] = -cons_links_aggr3.filter(like="Fischer").sum(axis=1)

heat_supply_buses_aggr["Retrofitting"] = gen_buses_aggr.filter(like="Retrofitting").sum(axis=1)
heat_supply_buses_aggr["Solar Thermal"] = gen_buses_aggr.filter(like="Solar Thermal")

heat_supply_cols = ["Retrofitting",
    "Air Heat Pump", "Ground Heat Pump",
    "Solar Thermal",
    "Biomass CHP",
     "Gas CHP", "Microgas CHP",
    "Gas Boiler", "Resistive Heater"]

#cols_to_plot = heat_supply_buses_aggr.columns.intersection(heat_supply_cols)
cols_to_plot = pd.Index(
    pd.Index(heat_supply_cols)
    .intersection(heat_supply_buses_aggr.columns)
    #.append(heat_supply_buses_aggr.columns.difference(heat_supply_cols))
)

plot_color = [tech_colors[c] for c in cols_to_plot]

with balance_plot_col:
    buses_el_area_plot = heat_supply_buses_aggr[cols_to_plot].hvplot.area(
        **kwargs,
        ylabel="Heat Supply [MW]",
        group_label=helper.config["links_t_parameter"]["p0"]["legend_title"],
        color=plot_color
        )
    #buses_el_line_plot = load_buses_aggr["electricity"].hvplot.line(color="#8B0000")
    #buses_el_area_plot = buses_el_area_plot * buses_el_line_plot
    buses_el_area_plot = buses_el_area_plot.opts(
        ylim=(0, None),
        active_tools=[],
        fontsize=plot_font_dict
    )
    s2=hv.render(buses_el_area_plot, backend="bokeh")
    st.bokeh_chart(s2, use_container_width=True)

tools.add_logo()
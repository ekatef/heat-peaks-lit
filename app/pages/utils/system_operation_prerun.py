# type: ignore
import os
import pathlib

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
import streamlit as st
import pages.utils.tools as tools
import typing

config=tools.config
pypsa_network_map=tools.get_network_map()

###### for generators #####################

def get_unique_carriers(df):
    """
    Extract carriers names from the columns names of df
    """
    all_cols=df.columns
    split_cols= []
    # TODO H2 for industry is captured as "for industry"
    for k in all_cols:
        carrier_name = re.sub("(.*?)(\d)", "", k).strip()
        split_cols.append(carrier_name)

    return list(set(split_cols))

@st.cache_resource
def get_meta_df(network_key):
    network=pypsa_network_map.get(network_key)
    return network.meta

@st.cache_resource
def get_gen_t_df(_pypsa_network, gen_t_key):
    """
    Get a dataframe of time-series of generation from pypsa_network
    for the parameter corresponding to gen_t_key
    """
    gen_t_df = _pypsa_network.generators_t[gen_t_key]
    unique_carriers = get_unique_carriers(gen_t_df)

    carriers_to_check = unique_carriers.copy()
    carriers_to_check.remove("solar")
    if any(name in carriers_to_check for name in config["carrier"].values()):
        resultant_df = gen_t_df 
    else:        
        unique_carriers_nice_names = [config["carrier"][carrier] for carrier in unique_carriers]
        resultant_df = pd.DataFrame(0, columns=unique_carriers_nice_names, index=gen_t_df.index)
        for carrier in unique_carriers:
            for bus_carrier in gen_t_df.columns:           
                if carrier in re.sub("(.*?)(\d)", "", bus_carrier).strip():  
                    nice_name = config["carrier"][carrier]
                    #nice_name = carrier
                    resultant_df[nice_name] += gen_t_df[bus_carrier]                 
    
    return resultant_df

# TODO Remove hardcoding?
# TODO Remove country hardcoding
@st.cache_resource
def get_buses_t_df(_pypsa_network, gen_t_key):

    #country_key = "PL"

    gen_t_df = _pypsa_network.generators_t[gen_t_key]
    unique_carriers = get_unique_carriers(gen_t_df)

    carriers_to_check = unique_carriers.copy()
    carriers_to_check.remove("solar")
    if any(name in carriers_to_check for name in config["carrier"].values()):
        return gen_t_df
    else:
        unique_carriers_nice_names = [config["carrier"][carrier] for carrier in unique_carriers]
        carriers_names_map = dict(zip(unique_carriers, unique_carriers_nice_names))
        new_columns = gen_t_df.columns
        for old, new in carriers_names_map.items():
            new_columns = new_columns.str.replace(old, new, regex=True)
        gen_t_df.columns = new_columns 

    return gen_t_df

non_empth_df_gen_t=[param for param in config["gen_t_parameter"]]
# @st.cache_resource
def get_gen_dict():

    result={}

    for network_key in pypsa_network_map.keys():
        network_dict={}
        network=pypsa_network_map.get(network_key)
        for non_empty_key in non_empth_df_gen_t:
            network_dict[non_empty_key]=get_gen_df(network, non_empty_key)

        result[network_key]=network_dict

    return result

# @st.cache_resource
def get_gen_t_dict():

    result={}
    
    for network_key in pypsa_network_map.keys():
        network_dict={}
        network=pypsa_network_map.get(network_key)
        for non_empty_key in non_empth_df_gen_t:
            network_dict[non_empty_key]=get_gen_t_df(network, non_empty_key)
        
        result[network_key]=network_dict
    
    return result

# @st.cache_resource
def get_buses_gen_t_dict():

    result={}
    
    for network_key in pypsa_network_map.keys():
        network_dict={}
        network=pypsa_network_map.get(network_key)
        for non_empty_key in non_empth_df_gen_t:
            network_dict[non_empty_key]=get_buses_t_df(network, non_empty_key)
        
        result[network_key]=network_dict
    
    return result

############# for load #####################
non_empty_load_keys = [param for param in config["loads_t_parameter"]]
non_empty_bus_key = [param for param in config["buses_t_parameter"]][0]

@st.cache_resource
def get_load_t_df(_pypsa_network, load_t_key):
    """
    Get a dataframe of time-series of load from pypsa_network
    for the parameter corresponding to load_t_key
    """
    load_t_df = _pypsa_network.loads_t[load_t_key]
    unique_carriers = get_unique_carriers(load_t_df)

    # electricity load is not captured by re as is doesn't have a sperific suffix
    unique_carriers = [s if s is not "" else "power" for s in unique_carriers]

    carriers_to_check = unique_carriers
    if any(name in carriers_to_check for name in config["carrier"].values()):    
        resultant_df = load_t_df 
    else:           
        unique_carriers_nice_names = [config["carrier"][carrier] for carrier in unique_carriers]
        resultant_df = pd.DataFrame(0, columns=unique_carriers_nice_names, index=load_t_df.index)

        for carrier in unique_carriers:
            for bus_carrier in load_t_df.columns:           
                if carrier in re.sub("(.*?)(\d)", "", bus_carrier).strip():  
                    nice_name = config["carrier"][carrier]
                    #nice_name = carrier
                    resultant_df[nice_name] += load_t_df[bus_carrier]                
    
    return resultant_df


# @st.cache_resource
def get_load_t_dict():
    """
    Get a list of load_t dataframes generation from pypsa_network
    for the parameter corresponding to all relevant keys (e.g. p)
    """
    
    result={}

    for network_key in pypsa_network_map.keys():
        network_dict={}
        network = pypsa_network_map.get(network_key)
        for non_empty_key in non_empty_load_keys:

            network_dict[non_empty_key] = get_load_t_df(network, non_empty_key)
            #network_dict[non_empty_key]=  rename_final_df(df)
        
        result[network_key]=network_dict
    return result

@st.cache_resource
def get_buses_load_t_df(_pypsa_network, load_t_key):

    load_t_df = _pypsa_network.loads_t[load_t_key]
    
    resultant_df = load_t_df

    unique_carriers = get_unique_carriers(load_t_df)
    # electricity load is not captured by re as is doesn't have a sperific suffix
    unique_carriers = [s if s is not "" else "power" for s in unique_carriers]

    carriers_to_check = unique_carriers
    if any(name in carriers_to_check for name in config["carrier"].values()):
        resultant_df = load_t_df
    else:    
        unique_carriers_nice_names = [config["carrier"][carrier] for carrier in unique_carriers]
        carriers_names_map = dict(zip(unique_carriers, unique_carriers_nice_names))
        new_columns = load_t_df.columns
        for old, new in carriers_names_map.items():
            new_columns = new_columns.str.replace(old, new, regex=True)
        load_t_df.columns = new_columns

        resultant_df = load_t_df

    return resultant_df


def get_marginal_costs(_pypsa_network, marginal_cost_key):

    result = _pypsa_network.buses_t[marginal_cost_key].T.groupby(
        [_pypsa_network.buses.country, _pypsa_network.buses.carrier]
    ).mean()

    return result


# @st.cache_resource  
def get_buses_load_t_dict():

    result={}
    
    for network_key in pypsa_network_map.keys():
        network_dict={}
        network=pypsa_network_map.get(network_key)
        for non_empty_key in non_empty_load_keys:
            network_dict[non_empty_key]=get_buses_load_t_df(network, non_empty_key)
        
        result[network_key]=network_dict
    
    return result


def get_marginal_costs_dict():

    result={}

    for network_key in pypsa_network_map.keys():
        network = pypsa_network_map.get(network_key)
        marginal_costs = get_marginal_costs(network, non_empty_bus_key)

        result[network_key] = marginal_costs

    return result

############## links
non_empth_df_links_t=[param for param in config["links_t_parameter"]]

@st.cache_resource
def get_buses_links_t_df(_pypsa_network, link_t_key):

    link_t_df = _pypsa_network.links_t[link_t_key]

    resultant_df = link_t_df

    unique_carriers = get_unique_carriers(link_t_df)
    # electricity link is not captured by re as is doesn't have a sperific suffix
    unique_carriers = [s if s is not "" else "power" for s in unique_carriers]

    carriers_to_check = unique_carriers
    if any(name in carriers_to_check for name in config["carrier"].values()):
        resultant_df = link_t_df
    else:
        unique_carriers_nice_names = [config["carrier"][carrier] for carrier in unique_carriers]
        carriers_names_map = dict(zip(unique_carriers, unique_carriers_nice_names))
        new_columns = link_t_df.columns
        for old, new in carriers_names_map.items():
            new_columns = new_columns.str.replace(old, new, regex=True)
        link_t_df.columns = new_columns

        resultant_df = link_t_df

    return resultant_df

# @st.cache_resource
def get_buses_links_t_dict():

    result={}

    for network_key in pypsa_network_map.keys():
        network_dict={}
        network=pypsa_network_map.get(network_key)
        for non_empty_key in non_empth_df_links_t:
            network_dict[non_empty_key]=get_buses_links_t_df(network, non_empty_key)

        result[network_key]=network_dict

    return result

def get_renamed_column(column_name):
    split_arr=column_name.split(" ")
    last=split_arr.pop(-1)
    split_arr.append(config["carrier"][last])
    return " ".join(split_arr)

def rename_final_df(df):
    for column_name in df.columns:
        df=df.rename(columns={column_name:get_renamed_column(column_name)})
    return df


# @st.cache_resource
def get_storage_t_dict():
    
    result={}

    for network_key in pypsa_network_map.keys():
        network_dict={}
        network = pypsa_network_map.get(network_key)
        for non_empty_key in non_empty_storage_keys:
            df=network.storage_units_t[non_empty_key].copy()
            network_dict[non_empty_key]=  rename_final_df(df)
        
        result[network_key]=network_dict
    return result

############# for links #####################
def get_links_unique_cols(pypsa_network, pypsa_component, col_name):
    #all_cols=pypsa_network.links_t["p0"].columns
    all_cols=getattr(pypsa_network, pypsa_component)[col_name].columns
    split_cols= []
    for k in all_cols:
        split_cols.append(k.split(" ")[-2]+" "+k.split(" ")[-1])
    return list(set(split_cols))

def get_links_df(pypsa_network, pypsa_component, component_key):
    #links_t_df=pypsa_network.links_t[links_t_key]
    pypsa_df = getattr(pypsa_network, pypsa_component)[component_key]
    unique_cols=get_links_unique_cols(pypsa_network, pypsa_component, component_key)
    resultant_df=pd.DataFrame(0,columns=unique_cols, index=pypsa_df.index)

    for carrier in unique_cols:
        for links_carrier in pypsa_df.columns:
            if carrier.split(" ")[-1] in links_carrier.split(" ") :
                resultant_df[carrier]+=pypsa_df[links_carrier]
    
    return resultant_df

#non_empth_links_keys=[param for param in config["links_t_parameter"]]
#non_empth_loads_keys=[param for param in config["loads_t_parameter"]]
#non_empth_stores_keys=[param for param in config["stores_t_parameter"]]

# @st.cache_resource
def get_components_t_dict(component_key, component_keys):
    result={}

    for network_key in pypsa_network_map.keys():
        network_dict={}
        network = pypsa_network_map.get(network_key)
        for non_empty_key in component_keys:
            network_dict[non_empty_key]=get_links_df(network, component_key, non_empty_key)
        
        result[network_key]=network_dict
    return result

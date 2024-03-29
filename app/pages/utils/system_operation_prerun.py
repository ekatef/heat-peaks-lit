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


#@st.cache_resource
def get_meta_df(network_key):
    network=pypsa_network_map.get(network_key)
    return network.meta

###### generators #####################

non_empth_df_gen_t=[param for param in config["gen_t_parameter"]]

#@st.cache_resource
def get_buses_gen_t_df(_pypsa_network, gen_t_key, country="all"):
    """
    Get a dataframe of time-series of generation from pypsa_network
    for the parameter corresponding to gen_t_key
    """
    gen_t_df = _pypsa_network.generators_t[gen_t_key].copy()
    if country != "all":
        gen_t_df = gen_t_df.filter(like=country)

    retrof_df = gen_t_df.filter(like = "retrofitting").copy()
    retrof_df["Retrofitting Urban Central"] = retrof_df.filter(like = "retrofitting").filter(like = "urban central heat").sum(axis=1)    
    retrof_df["Retrofitting Urban Decentral"] = retrof_df.filter(like = "retrofitting").filter(like = "urban decentral heat").sum(axis=1) 
    retrof_df["Retrofitting Rural"] = retrof_df.filter(like = "retrofitting").filter(like = "rural heat").sum(axis=1) 
    gen_t_df = (
        gen_t_df.T.groupby(_pypsa_network.generators.carrier).sum()
        .rename(index=config["carrier"])
    )
    gen_t_df = gen_t_df.groupby(gen_t_df.index).sum().T

    gen_t_df = pd.concat(
        [
            gen_t_df, 
            retrof_df[
                ["Retrofitting Urban Central",
                 "Retrofitting Urban Decentral",
                 "Retrofitting Rural"]
            ]
        ],
        axis=1
    )    

    return gen_t_df

#@st.cache_resource
def get_gen_dict():
    result={}

    for network_key in pypsa_network_map.keys():
        network_dict={}
        network=pypsa_network_map.get(network_key)
        for non_empty_key in non_empth_df_gen_t:
            network_dict[non_empty_key]=get_gen_df(network, non_empty_key)

        result[network_key]=network_dict

    return result

#@st.cache_resource
def get_buses_gen_t_dict(country="all"):

    result={}
    
    for network_key in pypsa_network_map.keys():
        network_dict={}
        network=pypsa_network_map.get(network_key)
        for non_empty_key in non_empth_df_gen_t:
            network_dict[non_empty_key]=get_buses_gen_t_df(network, non_empty_key, country)
        
        result[network_key]=network_dict
    
    return result

###### buses #####################
non_empty_bus_key = [param for param in config["buses_t_parameter"]][0]
#@st.cache_resource
def get_buses_load_t_dict(country="all"):
    """
    Get a list of load_t dataframes generation from pypsa_network
    for the parameter corresponding to all relevant keys (e.g. p)
    """
    
    result={}

    for network_key in pypsa_network_map.keys():
        network_dict={}
        network = pypsa_network_map.get(network_key)
        for non_empty_key in non_empty_load_keys:
            network_dict[non_empty_key] = get_buses_load_t_df(network, non_empty_key, country)
        result[network_key]=network_dict
    return result

def get_marginal_costs(_pypsa_network, marginal_cost_key, carrier, country):

    consider_carriers = config["carriers_for_marginal_costs"][carrier]["carrier"]
    consider_carriers = _pypsa_network.buses.query("carrier in @consider_carriers").index

    # TODO Add industry electricity
    #elec_industry = ['industry electricity']
    #n.buses.country = n.buses.location.apply(lambda b: b[0:2])
    #    n.loads["country"] = n.loads.bus.map(n.buses.country)
    #
    #    bus = n.buses.query("carrier in @carrier").index
    #    marginal_costs[name] = (
    #        n.buses_t.marginal_price[n.loads.query("carrier in @elec_industry").bus]
    #        .multiply(n.loads.query("carrier in @elec_industry").set_index("bus").p_set)
    #        .T.groupby(n.buses.country).sum().sum(axis=1)
    #        / n.loads.query("carrier in @elec_industry").groupby(n.loads.country).sum().p_set
    #        / 8760
    #    )    

    if carrier == "electricity":
        if country == 'all':
            result = _pypsa_network.buses_t[marginal_cost_key][consider_carriers].mean(axis=1)
        else:
            result = _pypsa_network.buses_t[marginal_cost_key][consider_carriers].filter(like=country).mean(axis=1)

    if carrier != "electricity":
        result = _pypsa_network.buses_t[marginal_cost_key][consider_carriers].mean(axis=1)

    return result

def get_weighted_costs(_pypsa_network, marginal_cost_key, carrier):

    consider_carriers = config["carriers_for_marginal_costs"][carrier]["carrier"]
    consider_carriers = _pypsa_network.buses.query("carrier in @consider_carriers").index

    if carrier == "electricity":
        result = pd.Series(index = _pypsa_network.buses.loc[consider_carriers].country.unique(), data=0)
        for country in result.index:
            result.loc[country] = (
                _pypsa_network.loads_t.p_set
                .multiply(_pypsa_network.buses_t.marginal_price)[consider_carriers]
                .filter(like = country).sum().sum() / _pypsa_network.loads_t.p_set.filter(like = country).sum().sum()
            )

    if carrier != "electricity":
        result = pd.Series(index=["Europe"], data=[_pypsa_network.buses_t[marginal_cost_key][consider_carriers].mean().mean()])

    return result

###### loads #####################
non_empty_load_keys = [param for param in config["loads_t_parameter"]]

# @st.cache_resource  
def get_buses_load_t_df(_pypsa_network, load_t_key, country="all"):
    """
    Get a dataframe of time-series of loads from pypsa_network
    for the parameter corresponding to load_t_key
    """
    load_t_df = _pypsa_network.loads_t[load_t_key].copy()

    if country != "all":
        #n.buses.country = n.buses.location.apply(lambda b: b[0:2])
        #n.loads["country"] = n.loads.bus.map(n.buses.country)
        #load_t_df = n.loads_t[load_t_key].T.groupby([n.loads.country, n.loads.carrier]).sum().T
        load_t_df = load_t_df.filter(like = country)
    
    load_t_df = (
        load_t_df.T.groupby(_pypsa_network.loads.carrier).sum()
        .rename(index=config["carrier"])
    )
    load_t_df = load_t_df.groupby(load_t_df.index).sum().T

    return load_t_df

###### costs #####################
def get_marginal_costs_dict(country):

    result={}

    for network_key in pypsa_network_map.keys():
        marginal_costs = {}
        network = pypsa_network_map.get(network_key)
        network.buses.country = network.buses.location.apply(lambda b: b.split(" ")[0][0:2])
        for carrier in config["carriers_for_marginal_costs"].keys():
            marginal_costs[carrier] = get_marginal_costs(network, non_empty_bus_key, carrier, country)

        result[network_key] = marginal_costs

    return result

def get_weighted_costs_dict():

    result={}

    for network_key in pypsa_network_map.keys():
        weighted_costs = {}
        network = pypsa_network_map.get(network_key)
        network.buses.country = network.buses.location.apply(lambda b: b.split(" ")[0][0:2])
        for carrier in config["carriers_for_marginal_costs"].keys():
            weighted_costs[carrier] = get_weighted_costs(network, non_empty_bus_key, carrier)

        result[network_key] = weighted_costs

    return result


############## links #####################
non_empth_df_links_t=[param for param in config["links_t_parameter"]]

#@st.cache_resource
def get_buses_links_t_df(_pypsa_network, link_t_key, country="all"):

    link_t_df = _pypsa_network.links_t[link_t_key].copy()

    if country != "all":
        link_t_df = link_t_df.filter(like=country)

    link_t_df = (
        link_t_df.T.groupby(_pypsa_network.links.carrier).sum()
        .rename(index=config["carrier"])
    )

    link_t_df = link_t_df.groupby(link_t_df.index).sum().T

    return link_t_df

def get_buses_links_t_dict(country="all"):
    """
    Get a dictionary for all the networks available in data
    """
    result={}

    for network_key in pypsa_network_map.keys():
        network_dict={}
        network=pypsa_network_map.get(network_key)
        for non_empty_key in non_empth_df_links_t:
            network_dict[non_empty_key]=get_buses_links_t_df(network, non_empty_key, country)

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

############# links #####################
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
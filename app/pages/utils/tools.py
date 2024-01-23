import os
import pathlib
import streamlit as st
import pypsa
import yaml

# @st.cache_resource
def open_yaml_file(config_file):
    with open(config_file, "r") as f:
       config = yaml.safe_load(f)
    return config

if pathlib.Path("pages/utils/config.yaml").is_file():
    config=open_yaml_file("pages/utils/config.yaml")
else:
    config=open_yaml_file("app/pages/utils/config.yaml")    


@st.cache_resource
def get_network_map():
    RESULTS_DIR = pathlib.Path(config["data_dir"], "results")
    networks = {}
    for dir in os.listdir(RESULTS_DIR):
        entry = pathlib.Path(RESULTS_DIR, dir)
        if not entry.is_dir():
            continue

        for dir_child in os.listdir(pathlib.Path(entry, "networks")):
            if not dir_child.endswith(".nc"):
                continue
            networks[dir] = pypsa.Network(
                pathlib.Path(entry, "networks", dir_child)
            )
    return networks

def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                background-image: url(https://github.com/pypsa-meets-earth/pypsa-kz-data/assets/53824825/ca7893de-26e2-47ad-a3e4-d91cd6716652);
                background-repeat: no-repeat;
                padding-top: 30px;
                background-position: 20px 20px;
                background-size: 120px;
            [data-testid="stSidebarNav"]::before {
                content: "test";
                margin-left: 20px;
                margin-top: 20px;
                font-size: 30px;
                position: relative;
                top: 100px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def rename_techs(label):
    prefix_to_remove = [
        "residential ",
        "services ",
        "urban ",
        "rural ",
        "central ",
        "decentral ",
    ]

    rename_if_contains = [
        "solid biomass CHP",
        "gas CHP",
        "gas boiler",
        "biogas",
        "solar thermal",
        "air heat pump",
        "ground heat pump",
        "resistive heater",
        "Fischer-Tropsch",
    ]

    rename_if_contains_dict = {
        "water tanks": "TES",
        "retrofitting": "building retrofitting",
        # "H2 Electrolysis": "hydrogen storage",
        # "H2 Fuel Cell": "hydrogen storage",
        # "H2 pipeline": "hydrogen storage",
        "battery": "battery storage",
        # "CC": "CC"
    }

    rename = {
        "Solar": "solar PV",
        "solar": "solar PV",
        "Sabatier": "methanation",
        "helmeth" : "methanation",
        "Offshore Wind (AC)": "offshore wind",
        "Offshore Wind (DC)": "offshore wind",
        "Onshore Wind": "onshore wind",
        "offwind-ac": "offshore wind",
        "offwind-dc": "offshore wind",
        "Run of River": "hydroelectricity",
        "Run of river": "hydroelectricity",
        "Reservoir & Dam": "hydroelectricity",
        "Pumped Hydro Storage": "hydroelectricity",
        "PHS": "hydroelectricity",
        "NH3": "ammonia",
        "co2 Store": "DAC",
        "co2 stored": "CO2 sequestration",
        "AC": "transmission lines",
        "DC": "transmission lines",
        "B2B": "transmission lines",
        "solid biomass for industry": "solid biomass",
        "solid biomass for industry CC": "solid biomass",
        "electricity distribution grid": "distribution lines",
        "Open-Cycle Gas":"OCGT",
        "gas": "gas storage",
        'gas pipeline new': 'gas pipeline',
        "gas for industry CC": "gas for industry",
        "SMR CC": "SMR",
        "process emissions CC": "process emissions",
        "Battery Storage": "battery storage",
        'H2 Store': "H2 storage",
        'Hydrogen Storage': "H2 storage",
        'co2 sequestered': "CO2 sequestration",
    }

    for ptr in prefix_to_remove:
        if label[: len(ptr)] == ptr:
            label = label[len(ptr) :]

    for rif in rename_if_contains:
        if rif in label:
            label = rif

    for old, new in rename_if_contains_dict.items():
        if old in label:
            label = new

    for old, new in rename.items():
        if old == label:
            label = new
    return label

import os
import pathlib
import streamlit as st
import pypsa
import yaml

#@st.cache_resource
def open_yaml_file(config_file):
    with open(config_file, "r") as f:
       config = yaml.safe_load(f)
    return config

if pathlib.Path("pages/utils/config.yaml").is_file():
    config=open_yaml_file("pages/utils/config.yaml")
else:
    config=open_yaml_file("app/pages/utils/config.yaml")    


#@st.cache_resource
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
                background-position: 40px 40px;
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

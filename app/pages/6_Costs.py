import streamlit as st
st.set_page_config(
    layout="wide"
)

import pages.utils.system_operation_prerun as helper
import pages.utils.tools as tools

import pandas as pd
import re
import plotly.graph_objects as go
import plotly.subplots as sp
import datetime

# needed to change cursor mode of selectboxes from the default text mode
fix_cursor_css = '''
    <style>
        .stSelectbox:first-of-type > div[data-baseweb="select"] > div {
            cursor: pointer;      
        }            
    </style>
'''

# carrier values per bus
gen_buses_dict_list = helper.get_buses_gen_t_dict()

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

st.title("Marginal costs")

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

buses_country_data = gen_buses_dict_list.get(selected_network)
gen_buses_df = buses_country_data["p"].drop("Load", axis=1, errors="ignore")

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

countries_codes = pd.unique(
    [(lambda x: re.sub("\d.*", '', x))(x) for x in gen_buses_df.columns]
)
# to avoid mis-interpretaiton of regex outputs
country_codes_clean = [x for x in countries_codes if x in helper.config["countries_names"].keys()]
with country_col:
    ctr = st.selectbox(
        "Country",
        country_codes_clean,
        format_func=country_formatter, 
        key="country",
        help="You can choose a country to examine operation of the energy system"
    )
    st.markdown(fix_cursor_css, unsafe_allow_html=True)  

# ###################### electricity costs #####################

costs_dict_list = helper.get_marginal_costs_dict()
costs = costs_dict_list.get(selected_network)

res_h = str(res) + "H"

costs = (
    costs.query("carrier == 'AC' and country == @ctr")
    .T[ctr].squeeze()
    .loc[values[0]:values[1]].resample(res_h).mean()
)

fig = sp.make_subplots(
    rows=1, cols=1,
)

fig.add_trace(
    go.Scatter(x=costs.index, y=costs.values,
    mode='lines'), row=1, col=1
)

st.plotly_chart(fig)

tools.add_logo()  
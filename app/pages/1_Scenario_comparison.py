import streamlit as st
st.set_page_config(
    layout="wide"
)
import sys
sys.path.append("app/")
import numpy as np
import pathlib
import plotly.express as px
import pages.utils.tools as tools
import pages.utils.scenario_comparision_prerun as helper
import pandas as pd
_, main_col, _, suppl_col, _ = st.columns([1, 35, 1, 20, 1])

data_color = "#333333"
# needed to change cursor mode of selectboxes from the default text mode
fix_cursor_css = '''
    <style>
        .stSelectbox:first-of-type > div[data-baseweb="select"] > div {
            cursor: pointer;      
        }            
    </style>
'''
# def rename_techs2(label):
#     prefix_to_remove = [
#         "residential ",
#         "services ",
#         "urban ",
#         "rural ",
#         "central ",
#         "decentral ",
#     ]

#     rename_if_contains = [
#         "solid biomass CHP",
#         "gas CHP",
#         "gas boiler",
#         "biogas",
#         "solar thermal",
#         "air heat pump",
#         "ground heat pump",
#         "resistive heater",
#         "Fischer-Tropsch",
#     ]

#     rename_if_contains_dict = {
#         "water tanks": "water tanks discharger",
#         "retrofitting": "building retrofitting",
#         # "H2 Electrolysis": "hydrogen storage",
#         # "H2 Fuel Cell": "hydrogen storage",
#         # "H2 pipeline": "hydrogen storage",
#         "battery": "battery storage",
#         # "CC": "CC"
#     }

#     rename = {
#         "Solar": "solar PV",
#         "solar": "solar PV",
#         "Sabatier": "methanation",
#         "helmeth" : "methanation",
#         "Offshore Wind (AC)": "offshore wind",
#         "Offshore Wind (DC)": "offshore wind",
#         "Onshore Wind": "onshore wind",
#         "offwind-ac": "offshore wind",  
#         "offwind-dc": "offshore wind",
#         "Run of River": "hydroelectricity",
#         "Run of river": "hydroelectricity",
#         "Reservoir & Dam": "hydroelectricity",
#         "Pumped Hydro Storage": "hydroelectricity",
#         "PHS": "hydroelectricity",
#         "NH3": "ammonia",
#         "co2 Store": "DAC",
#         "co2 stored": "CO2 sequestration",
#         "AC": "transmission lines",
#         "DC": "transmission lines",
#         "B2B": "transmission lines",
#         "solid biomass for industry": "solid biomass",
#         "solid biomass for industry CC": "solid biomass",
#         "electricity distribution grid": "distribution lines",
#         "Open-Cycle Gas":"OCGT",
#         "gas": "gas storage",
#         'gas pipeline new': 'gas pipeline',
#         "gas for industry CC": "gas for industry",
#         "SMR CC": "SMR",
#         "process emissions CC": "process emissions",
#         "Battery Storage": "battery storage",
#         'H2 Store': "H2 storage",
#         'Hydrogen Storage': "H2 storage",
#         'co2 sequestered': "CO2 sequestration",
#     }

#     for ptr in prefix_to_remove:
#         if label[: len(ptr)] == ptr:
#             label = label[len(ptr) :]

#     for rif in rename_if_contains:
#         if rif in label:
#             label = rif

#     for old, new in rename_if_contains_dict.items():
#         if old in label:
#             label = new

#     for old, new in rename.items():
#         if old == label:
#             label = new
#     return label


# preferred_order = pd.Index(
#     [
#         "solid biomass",
#         "solid biomass transport",
#         "biogas",
#         "gas for industry",
#         "methanol",
#         "oil",
        
#         "transmission lines",
#         "distribution lines",
#         "gas pipeline",
#         "H2 pipeline",
        
#         "H2 Electrolysis",
#         "H2 Fuel Cell",
#         "DAC",
#         "Fischer-Tropsch",
#         "methanation",
#         "BEV charger",
#         "V2G",
#         "SMR",
#         "methanolisation",
        
#         "TES",
#         "battery storage",
#         "gas storage",
#         "H2 storage",
#         "water tanks discharger",
        
#         "hydroelectricity",
#         "OCGT",
#         "onshore wind",
#         "offshore wind",
#         "solar PV",
#         "solar thermal",
#         "solar rooftop",
        
#         "solid biomass CHP",
#         "gas CHP",
#         "biomass boiler",
#         "gas boiler",
#         "resistive heater",
#         "air heat pump",
#         "ground heat pump",
        
#         "co2",
#         "CO2 sequestration",
#         "process emissions",

#         "building retrofitting"
#      ]
# )

def get_stat_unit(param):
    return tools.config["statistics_param_units"][param]

def get_carrier_map():
    return tools.config["carrier"]

def get_colors_map():
    return tools.config["tech_colors"]

def scenario_formatter(scenario):
    return tools.config["scenario_names"][scenario]

def main():
    st.title("Scenario comparison")

    network_map = tools.get_network_map()
    carriers_map = get_carrier_map()
    tech_map = dict(map(reversed, carriers_map.items()))
    

    ###### first dropdown plotting n.statistics #####
    params = list(network_map.values())[0].statistics()
    keep_columns = ["Capital Expenditure", "Operational Expenditure", "Curtailment", "Revenue"]
    params = params[keep_columns].columns.values

    st.header("Statistics plot")
    _, select_col, _ = st.columns([2,60,20])


    with select_col:
        option = st.selectbox(
            "Select metric",
            np.append(params, 'Total Costs'),
            help="You can select any parameter from PyPSA Network Statistics table"
        )
        st.markdown(fix_cursor_css, unsafe_allow_html=True)

    if option == "Total Costs":
        df = helper.get_df_for_parameter(
            network_map, ["Capital Expenditure", "Operational Expenditure"]
        )
    else:
        df = helper.get_df_for_parameter(
            network_map, option
        )

    new_cols = pd.Index(tools.config["preferred_order"]).intersection(df.columns).append(
        df.columns.difference(tools.config["preferred_order"])
    )
    df = df[new_cols].iloc[:,::-1]
    df_techs = [tech_map[c] for c in df.columns]
    tech_colors = get_colors_map()
    plot_color = [tech_colors[c] for c in df_techs]

    # needed to control markers size for the scatter
    _, plot_col, _ = st.columns([1, 80, 1])
    with plot_col:
        if option == "Capacity Factor":
            df["dummy_size"] = 1
            fig = px.scatter(df, y=df.columns,
                size="dummy_size",
                size_max=25,
                opacity=0.9,
                color_discrete_sequence=plot_color,
                labels={
                    "value":get_stat_unit(option),
                    "index":" ",
                    "variable": "carriers"
                },
                title=" ")
            helper.adjust_plot_appearance(current_fig=fig)
            st.plotly_chart(fig,
                use_cointainer_width=True
            )
            fig['data'][0]['showlegend']=True
        else:
            fig = px.bar(df, y=df.columns,
                #color_discrete_sequence=plot_color,                    
                labels={
                    "value":get_stat_unit(option),
                    "index":" ",
                    "variable": "carriers"
                }, 
                title=" ",
                color_discrete_sequence=plot_color,)
            helper.adjust_plot_appearance(current_fig=fig)
            st.plotly_chart(fig,
                use_cointainer_width=True
            )

    st.header("Network statistics")
    _, table_col, _ = st.columns([2, 60, 20])
    with table_col:
        scenario = st.selectbox(
            "Select scenario:",
            list(network_map.keys()),
            format_func=scenario_formatter,
            help="You can choose between available scenarios"
        )
    st.markdown(fix_cursor_css, unsafe_allow_html=True)
    stat_table = helper.add_statistics(network_map[scenario], keep_columns)

    th_props = [
        ("font-size", "18px"),
        ("color", data_color),
        ("font-weight", "bold"),
        ("text-align", "left")
    ]
    td_props = [
        ("font-size", "18px"),
        ("color", data_color)
    ]    
    styles = [
        dict(selector="th", props=th_props),
        dict(selector="td", props=td_props)
    ]

    df = (
        stat_table.style
        .format(precision=2, thousands=" ", decimal=".")
        .set_properties().set_table_styles(styles)
        )

    with table_col:
        # st.dataframe(stat_table.style.format(precision=2, thousands=" ", decimal="."))
        st.table(df)     

tools.add_logo()
main()



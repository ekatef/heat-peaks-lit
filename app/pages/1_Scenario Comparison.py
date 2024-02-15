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
    _, select_col, _ = st.columns([2, 60, 20])


    with select_col:
        option = st.selectbox(
            "Select metric",
            np.append(params, "Total Costs"),
            help="You can select a parameter to compare between scenarios"
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
    df = df[new_cols]
    #df_techs = [tech_map[c] for c in df.columns]
    df_techs = df.columns
    tech_colors = get_colors_map()
    plot_color = [tech_colors[c] for c in df_techs]

    df_sort = df.loc[df.sum(1).sort_values(ascending=False).index]
    
    scen_dict = tools.config["scenario_names"]
    # It doesn't look really good whan the bars are having long names
    #df_sort = df_sort.rename(index = scen_dict)

    # needed to control markers size for the scatter
    _, plot_col, _ = st.columns([1, 80, 1])
    with plot_col:
        if option == "Capacity Factor":
            df["dummy_size"] = 1
            fig = px.scatter(df_sort, y=df_sort.columns,
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
            fig = px.bar(df_sort, y=df_sort.columns,
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

    st.header("Considered scenarios")

    st.subheader("Notations")

    notations_df = pd.DataFrame(
        {
            "name": [
                "lvopt_rigid_i", 
                "lvopt_flex_i", 
                "lvop_retro_tes_i", 
                "lv1_flex_i", 
                "lv1_retro_tes_i", 
                "lvopt_rigid", 
                "lvopt_flex", 
                "lv1_flex"
            ],
            "Description": [
                "Supplied Heating Optimal Network Expansion",
                "Efficient Green Heating Optimal Network Expansion",
                "Efficient Heating Optimal Network Expansion",
                "Efficient Green Heating Limited Network Expansion",
                "Efficient Heating Scenario Limited Network Expansion",
                "Supplied Heating Optimal Network Expansion (no industry)",
                "Efficient Green Heating Optimal Network Expansion (no industry)",
                "Efficient Green Heating Limited Network Expansion (no industry)"
            ]
        },
        )

    notations_df.set_index("name", inplace=True)

    st.table(
        notations_df
            .style
            .set_properties().set_table_styles(styles)
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



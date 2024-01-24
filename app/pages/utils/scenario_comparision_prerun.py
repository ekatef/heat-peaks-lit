import pages.utils.tools as tools
import pandas as pd
import streamlit as st

data_color = "#1B1212"

# @st.cache_resource
# def get_df_for_parameter(_network_map, parameter, tech_name, _get_values_fn):
#     #all_column_names = _get_all_columns(_network_map, _get_cols_fn)
#     #all_column_names.discard("load")
#     #all_column_names = list(all_column_names)
#     df_array = []
#     indices = []

#     for key, n in _network_map.items():
#         #avilable_cols = _get_cols_fn(n)
#         #child_arr = []
#         #for col_name in all_column_names:
#         #    if col_name in avilable_cols:
#         #        child_arr.append(_get_values_fn(n, parameter, tech_name))
#         #    else:
#         #        child_arr.append(0)
#         child_arr = _get_values_fn(n, parameter, tech_name)
#         # it can easily happen that a requested technology is not available for a network
#         if len(child_arr) > 0:      
#             df_array.append(child_arr)
#             indices.append(key)

#     indices = [tools.config["scenario_names"][i] for i in indices]
#     nice_col_name=[]

#     wide_form_df = pd.DataFrame(df_array, index=indices)
#     # TODO Hard-coded nice names can be actually safier
#     wide_form_df.columns = wide_form_df.columns.droplevel(0)

#     return wide_form_df

def get_df_for_parameter(_network_map, parameter):

    result = pd.DataFrame()
    for key, n in _network_map.items():
        if isinstance(parameter, list):
            df = n.statistics()[parameter].dropna().sum(axis=1).droplevel(0).to_frame()
        else:
            df = n.statistics()[parameter].dropna().droplevel(0).to_frame()
        df.columns = [key]
        result = result.join(df, how="outer").fillna(0)

    result = result.groupby(result.index).sum()
    result = result.groupby(result.index.map(tools.rename_techs)).sum()
    drop = result.index[result.max(axis=1) < 0.005*result.sum().max()]
    result = result.drop(drop).T
    
    return result

def add_values_for_statistics(n, parameter, tech_list):
    df=n.statistics().loc[["Generator", "Link"]]
    return df.query('carrier in @tech_list')[parameter]

def add_statistics(n, keep_columns):
    return n.statistics()[keep_columns].loc["Generator"]


def add_values_for_co2(n, parameter, col_name):
    # https://github.com/PyPSA/PyPSA/issues/520
    # n.generators_t.p / n.generators.efficiency * n.generators.carrier.map(n.carriers.co2_emissions)
    df_p = n.generators_t.p
    df_p.drop(df_p.columns[df_p.columns.str.contains("load")], axis=1, inplace=True)
    df_gen = n.generators[~n.generators.index.str.contains("load")]
    co2 = (n.generators_t.p.mean(axis=0) / df_gen.efficiency ) * df_gen.carrier.map(n.carriers[parameter])
    if co2[co2.index.str.contains(col_name)].empty:
        return(0)
    else:
        return(co2[co2.index.str.contains(col_name)].iloc[0])


def add_values_for_generators(n, _parameter, col_name):
    return (
        n.generators.groupby(by="carrier")["p_nom_opt"]
        .sum()
        .drop("load", errors="ignore")
        .get(col_name, default=0)
    )


################
def get_stats_col_names(n):
    return n.statistics().index


def get_co2_col_names(n):
    return n.carriers.index.array


def get_gen_col_names(n):
    return n.generators.groupby(by="carrier")["p_nom"].sum().index.array

################
def _get_all_columns(network_map, get_cols_fn):
    names = set()
    for n in network_map.values():
        names = names | set(get_cols_fn(n))
    return names

def adjust_plot_appearance(current_fig):
    current_fig.update_layout(
        font=dict(
            family="PT Sans Narrow",
            size=18
        ),              
        legend_font_color=data_color,
        legend_font_size=18,
        legend_title_font_color=data_color,
        legend_title_font_size=18,
        font_color=data_color,
        height=800,
        width=800
    )
    current_fig.update_xaxes(
        tickangle=270,
        tickfont=dict(
            family="PT Sans Narrow",
            color=data_color,
            size=18
        )
    )
    current_fig.update_yaxes(
        title_font=dict(
            family="PT Sans Narrow",
            color=data_color,
            size=18                    
        ),
        tickfont=dict(
            family="PT Sans Narrow",
            color=data_color,
            size=18
        )
    )
    return(current_fig)


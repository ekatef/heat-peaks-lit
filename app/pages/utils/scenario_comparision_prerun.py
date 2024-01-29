import pages.utils.tools as tools
import pandas as pd
import streamlit as st

data_color = "#1B1212"

@st.cache_resource
def get_df_for_parameter(_network_map, parameter):

    result = pd.DataFrame()
    for key, n in _network_map.items():
        if isinstance(parameter, list):
            df = n.statistics()[parameter].dropna().sum(axis=1).droplevel(0).to_frame()
        else:
            df = n.statistics()[parameter].dropna().droplevel(0).to_frame()
        df.columns = [key]
        result = result.join(df, how="outer").fillna(0)

    tech_map = {item: item for item in result.index}
    tech_map |= tools.config["carrier"] # update tech mapping, if applicable
    result.index = result.index.map(tech_map)
    result = result.groupby(result.index).sum()
    drop = result.index[result.max(axis=1) < 0.005*result.sum().max()]
    result = result.drop(drop).T
    
    return result


#############
def add_values_for_statistics(n, parameter, col_name):
    return n.statistics()[parameter].loc["Generator"][col_name]

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
    return n.statistics()["Curtailment"].loc["Generator"].index


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
        width=800,
        legend={'traceorder':'reversed'}
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


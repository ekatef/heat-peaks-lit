
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.subplots as sp
import plotly.graph_objects as go

st.title("Modelling assumptions")

st.header("Assumptions for technology costs")

st.markdown(
    "Model assumptions are under constant revision."
    "Assumptions used for this study are basted on the "
    "[technology-data repository v0.6.2](https://github.com/PyPSA/technology-data/blob/master/outputs/costs_2030.csv). "
    "The most relevant technologies are outlined below:"
    ""
)

url = "https://raw.githubusercontent.com/PyPSA/technology-data/master/outputs/costs_2030.csv"
costs = pd.read_csv(url, index_col=0)

considered = [
    "central air-sourced heat pump", "decentral air-sourced heat pump",
    "central ground-sourced heat pump", "decentral ground-sourced heat pump",
    "central resistive heater", "decentral resistive heater",
    "central solar thermal", "decentral solar thermal",
    "central solid biomass CHP",
    "central water tank storage", "decentral water tank storage",
    "water tank charger", "water tank discharger",

    "battery inverter", "battery storage",
    "biogas upgrading", "direct air capture", "electricity distribution grid", "electricity grid connection",
    "electrolysis", "fuel cell", "central gas CHP", "central gas boiler",
    "decentral gas boiler", "hydrogen storage underground", "hydrogen storage tank type 1",
    "HVDC inverter pair", "helmeth", "micro CHP", "OCGT", "offwind",
    "onwind", "PHS", "ror", "methanation", "solar-rooftop",
    "solar-utility", "Steam methane reforming"
]

st.write(costs.loc[considered])

st.write("FOM is the fixed operation and maintenance costs. Given as percentage of overnight costs per annum.")
st.write("VOM is the Variable operation and maintenance costs.")

st.header("Assumptions to distribute heat demands")

url = 'https://raw.githubusercontent.com/PyPSA/pypsa-eur/v0.9.0/data/heat_load_profile_BDEW.csv'

heat_demand = pd.read_csv(url, index_col=0)

st.write("Deriving hourly space heating demand profiles is performed in three steps:")
st.write(
    "First, daily profiles are determined by applying the degree day approximation to each region. "
    "This involves utilizing daily averaged ambient air temperature data, where we assume heating above 15°C."
)
st.markdown(
    "Second, heat demands are distributed following average day patterns derived using the [demandlib](https://demandlib.readthedocs.io/en/latest/) package. "
    "They discriminate between a normal weekday or a weekend, and between the residential and the services sector. See the graphics below."
)

st.write("Third, the per unit time-series are scaled with the nationally reported heat demand per annum.")

#st.line_chart(heat_demand['residential space weekday'])
# Create an interactive plot with Plotly Express
fig = sp.make_subplots(
    rows=1, cols=1,
    #subplot_titles=['residential space weekday', 'residential space weekend', 'services space weekday', 'services space weekend']
)

fig.add_trace(go.Scatter(x=heat_demand.index, y=heat_demand["residential space weekday"], mode='lines', name=f'residential weekday'), row=1, col=1)
fig.add_trace(go.Scatter(x=heat_demand.index, y=heat_demand["residential space weekend"], mode='lines', name=f'residential weekend'), row=1, col=1)
fig.add_trace(go.Scatter(x=heat_demand.index, y=heat_demand["services space weekday"], mode='lines', name=f'services weekday'), row=1, col=1)
fig.add_trace(go.Scatter(x=heat_demand.index, y=heat_demand["services space weekend"], mode='lines', name=f'services weekend'), row=1, col=1)


fig.update_xaxes(title_text='number of hour in a day')
fig.update_yaxes(title_text='heat demand [per unit]')

# Display the interactive plot using Streamlit
st.plotly_chart(fig)

#st.header("Assumed heating demands per annum")

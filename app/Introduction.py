import base64
import geopandas as gpd
from PIL import Image
import plotly.express as px
import requests
import streamlit as st

import pages.utils.tools as tools

from io import BytesIO

# TODO Update the pictures
# demo-pictures from the global repo
url_1 = "https://openenergytransition.org/assets/img/projects/blog6-riccardo-annandale-unsplash.jpg"
#url_2 = "https://raw.githubusercontent.com/ekatef/assets/master/preview_2.png"
#url_3 = "https://raw.githubusercontent.com/ekatef/assets/master/preview_3.png"

@st.cache_data
def get_image(url):
    r = requests.get(url)
    return BytesIO(r.content)

def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                background-image: url(https://github.com/pypsa-meets-earth/pypsa-kz-data/assets/53824825/ca7893de-26e2-47ad-a3e4-d91cd6716652);
                background-repeat: no-repeat;
                padding-top: 30px;
                background-position: 20px 20px;
                background-size: 70px;
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

def resize_image(img, target_width, target_height, fill_color=(255, 255, 255)):
    aspect = img.width / img.height
    new_width = target_width
    new_height = target_height

    if aspect > 1:
        new_height = int(target_width / aspect)
    elif aspect < 1:
        new_width = int(target_height * aspect)

    img = img.resize((new_width, new_height), Image.LANCZOS)

    return(img)    

customized_button = st.markdown("""
    <style >
    .stDownloadButton, div.stButton {text-align:center}
    .stDownloadButton button, div.stButton > button:first-child {
        background-color: #F0F0F0;
        color:#000000;
        width: 150px;
        padding-left: 5px;
        padding-right: 5px;
    }
    
    .stDownloadButton button:hover, div.stButton > button:hover {
        background-color: #ADD8E6;
        color:#000000;
    }
        }
    </style>""", unsafe_allow_html=True)       

tools.add_logo()

st.title("Welcome to the Peak Demand Project!")

image_1 = Image.open(get_image(url=url_1))
#image_2 = Image.open(get_image(url=url_2))
#image_3 = Image.open(get_image(url=url_3))

image_1_resized = resize_image(image_1, 200, 300)
#image_2_resized = resize_image(image_2, 200, 300)
#image_3_resized = resize_image(image_3, 200, 300)

st.image(
    image_1_resized,
    #[image_1_resized, image_2_resized, image_3_resized], 
    width=200)

st.header("Select a page from the sidebar to get started")

st.subheader("This is a visualisation app of EEE project. You can view the code on [GitHub](https://github.com/martacki/heat-demand-peaks) and load the main results using a button bellow")

with open("app/assets/OET_presentation_template.pdf", "rb") as file:
    btn=st.download_button(
    label="Download EEE Preliminary Report",
    data=file,
    file_name="dowloaded.pdf",
    mime="application/octet-stream",
    help="Click here to download report as pdf",
    use_container_width=True
)

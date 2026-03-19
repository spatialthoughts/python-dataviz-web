import streamlit as st
import rioxarray as rxr
import xarray as xr
import numpy as np
import os
import folium
from streamlit_folium import st_folium
import matplotlib
import matplotlib.colors as mcolors

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
tif_path = os.path.join(BASE_DIR, 'bangalore_lulc_cog.tif')


@st.cache_data
def prepare_map_data():
    ds = rxr.open_rasterio(tif_path, masked=True)
    
    # Get bounds in WGS84
    left, bottom, right, top = ds.rio.bounds()
    if ds.rio.crs and ds.rio.crs.to_epsg() != 4326:
        import pyproj
        transformer = pyproj.Transformer.from_crs(ds.rio.crs, 'EPSG:4326', always_xy=True)
        left, bottom = transformer.transform(left, bottom)
        right, top = transformer.transform(right, top)
    bounds = [[bottom, left], [top, right]]
    center = [(bottom + top) / 2, (left + right) / 2]

    arr = ds.squeeze().values.astype(float)

    # Normalize LULC to [0, 1]; NaN stays NaN (folium renders transparent)
    lulc = np.clip((arr - 10) / (110 - 10), 0, 1)
    lulc[np.isnan(arr)] = np.nan

    return lulc, bounds, center


st.write('This is a simple Streamlit app to visualize raster data using Folium')

lulc, bounds, center = prepare_map_data()

m = folium.Map(location=center, zoom_start=12)

folium.raster_layers.ImageOverlay(
    image=lulc, bounds=bounds,
    colormap=matplotlib.colormaps['plasma'],
    opacity=0.7, name='LULC',
).add_to(m)

folium.LayerControl().add_to(m)

st_folium(m, height=600, use_container_width=True, returned_objects=[])

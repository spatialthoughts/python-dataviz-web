import streamlit as st
import rioxarray as rxr
import xarray as xr
import numpy as np
import os
import io
import base64
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

st.write('This is a simple Streamlit app to visualize raster data using Leafmap and Rioxarray.')

# Get the directory where app.py lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ds = rxr.open_rasterio(os.path.join(BASE_DIR, 'bangalore_lulc_cog.tif'), masked=True)


def raster_to_image_overlay(data, colormap_name, vmin=None, vmax=None, nodata=None):
    """Convert an xarray DataArray to a base64 PNG suitable for folium ImageOverlay."""
    arr = data.squeeze().values.astype(float)

    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)

    _vmin = vmin if vmin is not None else np.nanmin(arr)
    _vmax = vmax if vmax is not None else np.nanmax(arr)

    norm = mcolors.Normalize(vmin=_vmin, vmax=_vmax)
    cmap = plt.colormaps[colormap_name]
    rgba = cmap(norm(arr))  # shape (H, W, 4)

    # Make NaN pixels transparent
    nan_mask = np.isnan(arr)
    rgba[nan_mask, 3] = 0

    img = (rgba * 255).astype(np.uint8)

    buf = io.BytesIO()
    plt.imsave(buf, img, format='png')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    return f'data:image/png;base64,{b64}'


def get_bounds(data):
    """Return [[south, west], [north, east]] from a rioxarray DataArray."""
    left, bottom, right, top = data.rio.bounds()
    # reproject to WGS84 if needed
    if data.rio.crs and data.rio.crs.to_epsg() != 4326:
        import pyproj
        transformer = pyproj.Transformer.from_crs(data.rio.crs, 'EPSG:4326', always_xy=True)
        left, bottom = transformer.transform(left, bottom)
        right, top = transformer.transform(right, top)
    return [[bottom, left], [top, right]]


bounds = get_bounds(ds)
center = [(bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2]

m = folium.Map(location=center, zoom_start=12)

# Layer 1: LULC
lulc_url = raster_to_image_overlay(ds, 'plasma', vmin=10, vmax=110, nodata=np.nan)
folium.raster_layers.ImageOverlay(
    image=lulc_url,
    bounds=bounds,
    opacity=0.7,
    name='LULC',
    interactive=True,
).add_to(m)

# Layer 2: Built-up (values == 50)
processed = xr.where(ds == 50, 1, 0)
processed.rio.write_crs(ds.rio.crs, inplace=True)
built_url = raster_to_image_overlay(processed, 'Reds', vmin=0, vmax=1, nodata=0)
folium.raster_layers.ImageOverlay(
    image=built_url,
    bounds=bounds,
    opacity=0.7,
    name='Built',
    interactive=True,
).add_to(m)

folium.LayerControl().add_to(m)

st_folium(m, height=600, use_container_width=True)

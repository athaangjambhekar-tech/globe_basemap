import json
import requests
import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------------
# 1. Base rotating globe
# ---------------------------------------------------------------
fig = go.Figure()
fig.add_trace(go.Scattergeo())  # base layer so geo settings apply

fig.update_geos(
    projection_type="orthographic",
    projection_rotation=dict(lon=80, lat=22),  # start centered on India
    showland=True,
    landcolor="rgb(79,126,201)",
    showocean=True,
    oceancolor="rgb(238,240,242)",
    showcountries=True,
    countrycolor="white",
    coastlinecolor="white",
    showsubunits=False,
    showlakes=True,
    lakecolor="rgb(238,240,242)",
    showframe=False,
    lataxis_showgrid=True,
    lonaxis_showgrid=True,
    lataxis_gridcolor="rgba(150,150,150,0.3)",
    lonaxis_gridcolor="rgba(150,150,150,0.3)",
)

def polygons_of(geom):
    return geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]

def largest_ring(geom):
    rings = [np.array(ring) for poly in polygons_of(geom) for ring in poly]
    return max(rings, key=len)

# ---------------------------------------------------------------
# 2. India STATE boundaries + names (one trace each, as before)
# ---------------------------------------------------------------
state_geojson = requests.get(
    "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/"
    "raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
).json()

STATE_NAME_KEYS = ["st_nm", "ST_NM", "NAME_1", "name", "NAME"]
def get_name(props, keys):
    for k in keys:
        if k in props:
            return props[k]
    return "Unknown"

s_border_lon, s_border_lat = [], []
s_label_lon, s_label_lat, s_label_name = [], [], []

for f in state_geojson["features"]:
    for poly in polygons_of(f["geometry"]):
        for ring in poly:
            arr = np.array(ring)
            s_border_lon.extend(arr[:, 0].tolist()); s_border_lon.append(None)
            s_border_lat.extend(arr[:, 1].tolist()); s_border_lat.append(None)
    ring = largest_ring(f["geometry"])
    s_label_lon.append(ring[:, 0].mean())
    s_label_lat.append(ring[:, 1].mean())
    s_label_name.append(get_name(f.get("properties", {}), STATE_NAME_KEYS))

fig.add_trace(go.Scattergeo(
    lon=s_border_lon, lat=s_border_lat, mode="lines",
    line=dict(width=1, color="rgba(255,255,255,0.9)"),
    hoverinfo="skip", showlegend=False, name="state_borders",
))
fig.add_trace(go.Scattergeo(
    lon=s_label_lon, lat=s_label_lat, text=s_label_name, mode="text",
    textfont=dict(size=8, color="white"),
    hoverinfo="skip", showlegend=False, name="state_labels",
))

# ---------------------------------------------------------------
# 3. India DISTRICT names — labels only, no boundaries drawn
#    (district polygons are far more detailed; skipping the lines
#    keeps the point count, and the lag, way down)
# ---------------------------------------------------------------
try:
    district_geojson = requests.get(
        "https://raw.githubusercontent.com/datameet/maps/master/Districts/2011_Dist.geojson"
    ).json()

    DISTRICT_NAME_KEYS = ["DISTRICT", "District", "dtname", "DtName", "district", "NAME_2"]
    d_label_lon, d_label_lat, d_label_name = [], [], []

    for f in district_geojson["features"]:
        ring = largest_ring(f["geometry"])
        d_label_lon.append(ring[:, 0].mean())
        d_label_lat.append(ring[:, 1].mean())
        d_label_name.append(get_name(f.get("properties", {}), DISTRICT_NAME_KEYS))

    fig.add_trace(go.Scattergeo(
        lon=d_label_lon, lat=d_label_lat, text=d_label_name, mode="text",
        textfont=dict(size=5, color="rgba(255,255,255,0.85)"),
        hoverinfo="skip", showlegend=False, name="district_labels",
        visible=True,  # shown by default
    ))
    district_trace_index = len(fig.data) - 1
except Exception as e:
    print(f"Could not load district data: {e}")
    district_trace_index = None

# ---------------------------------------------------------------
# 4. Optional hide button — flip on if 700+ labels feel heavy
#    while dragging; leaves the choice in your hands at runtime
#    instead of always paying the render cost or never having it.
# ---------------------------------------------------------------
if district_trace_index is not None:
    n = len(fig.data)
    show_mask = [True] * n
    hide_mask = [True] * n
    hide_mask[district_trace_index] = False

    fig.update_layout(
        updatemenus=[dict(
            type="buttons",
            direction="right",
            x=0.5, y=1.08, xanchor="center",
            buttons=[
                dict(label="Show districts", method="restyle",
                     args=[{"visible": show_mask}]),
                dict(label="Hide districts", method="restyle",
                     args=[{"visible": hide_mask}]),
            ],
        )]
    )

fig.update_layout(
    title="Drag to rotate — India states + districts",
    margin=dict(l=0, r=0, t=60, b=0),
    height=750,
)

fig.show()
# fig.write_html("globe.html")

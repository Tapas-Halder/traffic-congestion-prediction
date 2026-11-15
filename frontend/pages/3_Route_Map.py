"""Classic TrafficIQ Kolkata map and route UI restored from the earlier dashboard design."""
from __future__ import annotations

import os
import requests
import folium
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="TrafficIQ | Kolkata Map & Route", page_icon="🚦", layout="wide")

try:
    BACKEND_URL = str(os.getenv("BACKEND_URL") or st.secrets.get("BACKEND_URL", "")).strip().rstrip("/")
except Exception:
    BACKEND_URL = str(os.getenv("BACKEND_URL", "")).strip().rstrip("/")

LOCATIONS = [
    {"name": "Esplanade", "lat": 22.5646, "lon": 88.3510},
    {"name": "Park Street", "lat": 22.5535, "lon": 88.3520},
    {"name": "Howrah Bridge", "lat": 22.5851, "lon": 88.3468},
    {"name": "EM Bypass", "lat": 22.5395, "lon": 88.3960},
    {"name": "Salt Lake", "lat": 22.5726, "lon": 88.4338},
]
PLACE_COORDS = {p["name"]: (p["lat"], p["lon"]) for p in LOCATIONS}
KNOWN_PLACES = list(PLACE_COORDS)
CENTER = (22.5726, 88.3639)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#08111f;--panel:#111d2e;--line:#263850;--muted:#91a4bc;--blue:#4da3ff}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:radial-gradient(ellipse at 15% 0%,#142c49 0%,#08111f 42%,#070d18 100%);color:#edf5ff}
[data-testid="stHeader"]{background:rgba(8,17,31,.72)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#101d30 0%,#0b1524 100%);border-right:1px solid #263850}
[data-testid="stSidebar"] *{color:#dce9f8}
.block-container{max-width:1500px;padding-top:2.1rem;padding-bottom:3rem}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.035em;color:#f3f8ff}
h1{font-size:2.35rem!important;font-weight:700!important}
h2{font-size:1.55rem!important}h3{font-size:1.12rem!important}
p,label,.stCaption{color:#a9bad0}
.stButton>button{border-radius:10px;border:1px solid #3977b7;background:linear-gradient(110deg,#1768b4,#258fc4);color:white;font-weight:700;min-height:42px}
div[data-testid="stMetric"]{background:linear-gradient(145deg,#17283e,#101c2d);border:1px solid #2a405b;padding:15px 17px;border-radius:15px}
div[data-testid="stMetricLabel"]{color:#91a4bc}
div[data-testid="stMetricValue"]{color:#f3f8ff;font-family:'Space Grotesk',sans-serif}
.stTabs [data-baseweb="tab-list"]{gap:8px;border-bottom:1px solid #263850}
.stTabs [data-baseweb="tab"]{background:#101d2e;border:1px solid #263850;border-radius:10px 10px 0 0;padding:10px 16px;color:#9fb2c9}
.stTabs [aria-selected="true"]{background:#183452!important;color:#73c5ff!important;border-color:#3977b7!important}
div[data-testid="stVerticalBlockBorderWrapper"]{border-color:#263850!important;border-radius:15px!important;background:rgba(17,29,46,.55)}
.stAlert{border-radius:12px}
input,textarea,[data-baseweb="select"]>div{background:#101d2e!important;border-color:#314761!important}
hr{border-color:#263850!important}
@media(max-width:700px){.block-container{padding:1rem .8rem 2rem}h1{font-size:1.8rem!important}}
</style>
""", unsafe_allow_html=True)


def api_get(path, params=None):
    if not BACKEND_URL.startswith(("http://", "https://")):
        raise RuntimeError("BACKEND_URL is missing. Set it in Streamlit Community Cloud Secrets.")
    response = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def find_value(obj, names):
    wanted = {x.lower().replace("_", "").replace("-", "") for x in names}
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower().replace("_", "").replace("-", "") in wanted and isinstance(value, (int, float)):
                return float(value)
        for value in obj.values():
            found = find_value(value, names)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_value(value, names)
            if found is not None:
                return found
    return None


def traffic_status(current, free):
    if current is None or free is None or free <= 0:
        return None
    ratio = current / free
    if ratio >= 0.90:
        return "Low"
    if ratio >= 0.70:
        return "Moderate"
    return "Heavy"


def status_color(status):
    return {"Low": "#34d47a", "Moderate": "#f58542", "Heavy": "#f54242", None: "#7b82a0"}[status]


@st.cache_data(ttl=60, show_spinner=False)
def fetch_location(base_url, lat, lon):
    response = requests.get(
        f"{base_url}/api/v1/data/current",
        params={"latitude": lat, "longitude": lon},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_route(base_url, lat1, lon1, lat2, lon2):
    response = requests.get(
        f"{base_url}/api/v1/route",
        params={"from_lat": lat1, "from_lon": lon1, "to_lat": lat2, "to_lon": lon2},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


st.title("🚦 TrafficIQ — Kolkata")
st.caption("Live traffic map and road route planner")

with st.sidebar:
    st.markdown("## 🚦 TrafficIQ")
    st.caption("Kolkata traffic congestion")
    if st.button("↻ Refresh map and route data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Traffic: TomTom API · Road route: TomTom / OpenStreetMap")

tab_map, tab_route = st.tabs(["📍 Kolkata Traffic Map", "🧭 Road Route Planner"])

with tab_map:
    st.markdown("#### Kolkata — traffic status by location")
    st.caption("Select a marker to see the latest available speed information.")
    traffic_map = folium.Map(location=CENTER, zoom_start=12, tiles="OpenStreetMap", control_scale=True)
    statuses = []
    with st.spinner("Fetching live traffic information for Kolkata..."):
        for place in LOCATIONS:
            try:
                payload = fetch_location(BACKEND_URL, place["lat"], place["lon"])
                current = find_value(payload, ["currentSpeed", "current_speed"])
                free = find_value(payload, ["freeFlowSpeed", "free_flow_speed"])
                status = traffic_status(current, free)
                error = None
            except Exception as exc:
                current, free, status, error = None, None, None, str(exc)
            statuses.append((place, current, free, status, error))
            speed_text = f"{current:.0f} km/h" if current is not None else "Data unavailable"
            free_text = f"{free:.0f} km/h" if free is not None else "Data unavailable"
            body = (f"<b>{place['name']}</b><br>{status or 'Data unavailable'}<br>"
                    f"Current: {speed_text}<br>Free-flow: {free_text}")
            color = {"Low": "green", "Moderate": "orange", "Heavy": "red", None: "gray"}[status]
            folium.CircleMarker(
                location=[place["lat"], place["lon"]], radius=12,
                color=status_color(status), weight=3, fill=True,
                fill_color=status_color(status), fill_opacity=0.65,
                tooltip=f"{place['name']} — {status or 'Data unavailable'}",
                popup=folium.Popup(body, max_width=240),
            ).add_to(traffic_map)

    legend = "".join(
        f'<span style="color:{status_color(s)}">●</span> {label}<br>'
        for s, label in [("Low", "Light traffic"), ("Moderate", "Moderate traffic"),
                         ("Heavy", "Heavy traffic"), (None, "Data unavailable")]
    )
    traffic_map.get_root().html.add_child(folium.Element(
        '<div style="position:fixed;bottom:24px;left:24px;background:#1e2435;border:1px solid #222838;'
        'border-radius:10px;padding:10px 14px;font-size:12px;color:#eef0f6;z-index:1000">'
        f"{legend}</div>"))
    st_folium(traffic_map, height=480, use_container_width=True,
              returned_objects=[], key="classic_kolkata_map")
    st.caption("Marker colour is based on the current and free-flow speeds returned by the live traffic service. Grey means data is unavailable.")
    cols = st.columns(len(statuses))
    for col, (place, current, free, status, error) in zip(cols, statuses):
        with col:
            st.metric(place["name"], status or "Unavailable",
                      f"{current:.0f} km/h" if current is not None else "No speed data")

with tab_route:
    st.markdown("#### Plan a road route across Kolkata")
    st.caption("Choose two locations to see the road route and available traffic information.")
    r1, r2 = st.columns(2)
    from_place = r1.selectbox("🟢 Starting point", KNOWN_PLACES, index=0, key="classic_route_from")
    to_place = r2.selectbox("🔴 Destination", KNOWN_PLACES, index=min(2, len(KNOWN_PLACES)-1), key="classic_route_to")
    st.caption("🟢 Light traffic  ·  🟠 Moderate traffic  ·  🔴 Heavy traffic  ·  ⚪ Data unavailable")

    if from_place == to_place:
        st.info("Choose two different locations.")
    elif st.button("Show road route", type="primary", use_container_width=True):
        (lat1, lon1), (lat2, lon2) = PLACE_COORDS[from_place], PLACE_COORDS[to_place]
        try:
            with st.spinner("Loading road route and traffic information..."):
                route_data = fetch_route(BACKEND_URL, lat1, lon1, lat2, lon2)
            coords = route_data.get("coordinates") or []
            samples = route_data.get("samples") or []
            distance = route_data.get("distance_meters")
            travel_time = route_data.get("travel_time_seconds")
            delay = route_data.get("traffic_delay_seconds")
            provider = route_data.get("route_provider", "tomtom")

            if provider == "osrm":
                st.info("Road map is provided by OpenStreetMap. A live traffic-aware travel time is not available for this route.")
            c1, c2, c3 = st.columns(3)
            c1.metric("Road distance", f"{distance/1000:.1f} km" if isinstance(distance, (int, float)) else "Unavailable")
            c2.metric("Estimated travel time", f"{round(travel_time/60)} min" if isinstance(travel_time, (int, float)) else "Unavailable")
            c3.metric("Traffic delay", f"{round(delay/60)} min" if isinstance(delay, (int, float)) else "Unavailable")

            if len(coords) < 2:
                st.warning("A road route is not available for these locations right now.")
            else:
                route_map = folium.Map(location=[(lat1+lat2)/2, (lon1+lon2)/2],
                                       zoom_start=12, tiles="OpenStreetMap")
                colors = {"low": "#34d47a", "moderate": "#f58542",
                          "heavy": "#f54242", "unavailable": "#7b82a0"}
                if samples:
                    for i, sample in enumerate(samples):
                        left = 0 if i == 0 else (samples[i-1]["index"] + sample["index"]) // 2
                        right = len(coords)-1 if i == len(samples)-1 else (sample["index"] + samples[i+1]["index"]) // 2
                        if right > left:
                            folium.PolyLine(
                                coords[left:right+1],
                                color=colors.get(sample.get("status"), "#7b82a0"),
                                weight=6, opacity=0.85,
                                tooltip="Sampled traffic: " + str(sample.get("status", "unavailable")),
                            ).add_to(route_map)
                else:
                    folium.PolyLine(coords, color="#7b82a0", weight=6, opacity=0.85).add_to(route_map)
                folium.Marker([lat1, lon1], tooltip="From: " + from_place,
                              icon=folium.Icon(color="green")).add_to(route_map)
                folium.Marker([lat2, lon2], tooltip="To: " + to_place,
                              icon=folium.Icon(color="red")).add_to(route_map)
                route_map.fit_bounds(coords)
                st_folium(route_map, height=480, use_container_width=True,
                          returned_objects=[], key="classic_road_route_map")
            st.caption("Traffic colours are sampled estimates along the road route, not continuous measurements of every road segment.")
        except requests.HTTPError as exc:
            detail = exc.response.text[:300] if exc.response is not None else str(exc)
            st.error(f"Road route unavailable: {detail}")
        except Exception as exc:
            st.error(f"Could not load the road route: {exc}")

st.divider()
st.caption("TrafficIQ · Kolkata · Live data depends on TomTom and backend availability.")

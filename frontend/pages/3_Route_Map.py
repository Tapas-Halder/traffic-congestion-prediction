"""Interactive Kolkata map and road-to-road route planner."""
from __future__ import annotations

import os
import requests
import folium
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="TrafficIQ | Kolkata Map", page_icon="🗺️", layout="wide")

try:
    BACKEND_URL = str(os.getenv("BACKEND_URL") or st.secrets.get("BACKEND_URL", "")).strip().rstrip("/")
except Exception:
    BACKEND_URL = str(os.getenv("BACKEND_URL", "")).strip().rstrip("/")

LOCATIONS = {
    "Esplanade": (22.5646, 88.3510),
    "Park Street": (22.5535, 88.3520),
    "Howrah Bridge": (22.5851, 88.3468),
    "EM Bypass": (22.5395, 88.3960),
    "Salt Lake": (22.5726, 88.4338),
}
COLORS = {"Light": "green", "Moderate": "orange", "Heavy": "red", "Unavailable": "gray"}


def request_json(path: str, *, params: dict | None = None):
    if not BACKEND_URL.startswith(("https://", "http://")):
        raise RuntimeError("Backend connection is not configured. Set BACKEND_URL in Streamlit Cloud Secrets.")
    response = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=45)
    response.raise_for_status()
    return response.json()


def get_number(data, keys):
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
        for value in data.values():
            found = get_number(value, keys)
            if found is not None:
                return found
    elif isinstance(data, list):
        for value in data:
            found = get_number(value, keys)
            if found is not None:
                return found
    return None


def get_traffic_status(current, free):
    if current is None or free is None or free <= 0:
        return "Unavailable"
    ratio = current / free
    if ratio >= 0.90:
        return "Light"
    if ratio >= 0.70:
        return "Moderate"
    return "Heavy"


@st.cache_data(ttl=60, show_spinner=False)
def load_location_traffic(name: str, lat: float, lon: float):
    data = request_json("/api/v1/data/current", params={"latitude": lat, "longitude": lon})
    current = get_number(data, ["currentSpeed", "current_speed"])
    free = get_number(data, ["freeFlowSpeed", "free_flow_speed"])
    return {"name": name, "current": current, "free": free,
            "status": get_traffic_status(current, free)}


@st.cache_data(ttl=300, show_spinner=False)
def load_route(from_lat: float, from_lon: float, to_lat: float, to_lon: float):
    return request_json("/api/v1/route", params={
        "from_lat": from_lat, "from_lon": from_lon,
        "to_lat": to_lat, "to_lon": to_lon,
    })


st.title("🗺️ Kolkata Live Map & Route Planner")
st.caption("Explore road conditions and view a road route between two Kolkata locations.")

tab_map, tab_route = st.tabs(["📍 Kolkata Traffic Map", "🧭 Plan a Route"])

with tab_map:
    st.subheader("Traffic across selected Kolkata areas")
    st.caption("Marker colours: green = moving well · orange = moderate · red = heavy · grey = unavailable")
    if st.button("↻ Refresh map data", key="refresh_map"):
        st.cache_data.clear()
        st.rerun()

    rows = []
    with st.spinner("Loading current road information from the backend..."):
        for name, (lat, lon) in LOCATIONS.items():
            try:
                rows.append(load_location_traffic(name, lat, lon))
            except Exception:
                rows.append({"name": name, "current": None, "free": None, "status": "Unavailable"})

    traffic_map = folium.Map(location=[22.5726, 88.3639], zoom_start=12, tiles="OpenStreetMap")
    for row in rows:
        lat, lon = LOCATIONS[row["name"]]
        speed = f'{row["current"]:.0f} km/h' if row["current"] is not None else "Not available"
        folium.Marker(
            [lat, lon],
            tooltip=row["name"],
            popup=f'<b>{row["name"]}</b><br>Traffic: {row["status"]}<br>Current speed: {speed}',
            icon=folium.Icon(color=COLORS[row["status"]], icon="road", prefix="fa"),
        ).add_to(traffic_map)
    st_folium(traffic_map, height=500, use_container_width=True,
              returned_objects=[], key="kolkata_live_traffic_map")

    cols = st.columns(len(rows))
    for col, row in zip(cols, rows):
        with col:
            speed = f'{row["current"]:.0f} km/h' if row["current"] is not None else "—"
            st.metric(row["name"], row["status"], speed)

with tab_route:
    st.subheader("Find a road route")
    left, right = st.columns(2)
    names = list(LOCATIONS)
    origin = left.selectbox("Starting point", names, index=0, key="route_origin")
    destination = right.selectbox("Destination", names, index=2, key="route_destination")

    if origin == destination:
        st.info("Please choose two different locations.")
    elif st.button("Show route on map", type="primary", use_container_width=True):
        start = LOCATIONS[origin]
        end = LOCATIONS[destination]
        try:
            with st.spinner("Finding the road route..."):
                route = load_route(start[0], start[1], end[0], end[1])
            coords = route.get("coordinates") or []
            if len(coords) < 2:
                st.warning("A road route is not available for these locations right now.")
            else:
                provider = route.get("route_provider", "unknown")
                distance = route.get("distance_meters")
                travel_time = route.get("travel_time_seconds")
                delay = route.get("traffic_delay_seconds")
                a, b, c = st.columns(3)
                a.metric("Road distance", f"{distance / 1000:.1f} km" if isinstance(distance, (int, float)) else "Unavailable")
                b.metric("Travel time", f"{round(travel_time / 60)} min" if isinstance(travel_time, (int, float)) else "Unavailable")
                c.metric("Traffic delay", f"{round(delay / 60)} min" if isinstance(delay, (int, float)) else "Unavailable")

                route_map = folium.Map(location=coords[len(coords)//2], zoom_start=12, tiles="OpenStreetMap")
                samples = route.get("samples") or []
                sample_colors = {"low": "#24a148", "moderate": "#f1a208", "heavy": "#da1e28", "unavailable": "#64748b"}
                if samples:
                    for index, sample in enumerate(samples):
                        left_i = 0 if index == 0 else (samples[index-1]["index"] + sample["index"]) // 2
                        right_i = len(coords)-1 if index == len(samples)-1 else (sample["index"] + samples[index+1]["index"]) // 2
                        segment = coords[left_i:right_i+1]
                        if len(segment) >= 2:
                            folium.PolyLine(segment, color=sample_colors.get(sample.get("status"), "#64748b"),
                                            weight=7, opacity=0.9).add_to(route_map)
                else:
                    folium.PolyLine(coords, color="#2563eb", weight=7, opacity=0.9).add_to(route_map)
                folium.Marker(coords[0], tooltip=f"Start: {origin}",
                              icon=folium.Icon(color="green", icon="play")).add_to(route_map)
                folium.Marker(coords[-1], tooltip=f"Destination: {destination}",
                              icon=folium.Icon(color="red", icon="flag")).add_to(route_map)
                route_map.fit_bounds(coords)
                st_folium(route_map, height=500, use_container_width=True,
                          returned_objects=[], key="kolkata_route_result_map")
                if provider == "osrm":
                    st.info("Route geometry is from OpenStreetMap/OSRM. Live traffic-aware travel time is not available for this route.")
                st.caption("Traffic colours are based on a small number of TomTom observations along the route; they are estimates, not a reading of every metre of road.")
        except requests.HTTPError as exc:
            detail = exc.response.text[:300] if exc.response is not None else str(exc)
            st.error(f"Route service returned an error: {detail}")
        except Exception as exc:
            st.error(f"Could not load the route: {exc}")

st.caption("TrafficIQ · Kolkata · Live information depends on the availability of the connected data services.")

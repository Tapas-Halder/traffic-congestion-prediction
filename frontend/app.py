import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium
import requests
import random
import time
from datetime import datetime, timedelta

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TrafficIQ — Congestion Prediction",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS (dark theme matching HTML dashboard) ───────────────────────────
st.markdown("""
<style>
  /* Global dark background */
  .stApp { background-color: #0e1117; color: #eef0f6; }
  [data-testid="stSidebar"] { background-color: #171c27; border-right: 1px solid #222838; }

  /* Metric cards */
  [data-testid="metric-container"] {
    background: #171c27;
    border: 1px solid #222838;
    border-radius: 14px;
    padding: 16px 20px;
  }
  [data-testid="stMetricValue"]  { color: #eef0f6; font-size: 26px !important; }
  [data-testid="stMetricLabel"]  { color: #7b82a0; font-size: 12px !important; }
  [data-testid="stMetricDelta"]  { font-size: 11px !important; }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"]  { background: #171c27; border-radius: 10px; gap:4px; }
  .stTabs [data-baseweb="tab"]       { background: transparent; color: #7b82a0; border-radius: 8px; font-weight:500; }
  .stTabs [aria-selected="true"]     { background: #222838 !important; color: #eef0f6 !important; }

  /* Dataframe */
  [data-testid="stDataFrame"] { border: 1px solid #222838; border-radius: 12px; overflow: hidden; }

  /* Info / warning boxes */
  .stAlert { border-radius: 12px; }

  /* Divider */
  hr { border-color: #222838; }

  /* Buttons */
  .stButton > button {
    background: #4e9fff; color: #fff; border: none;
    border-radius: 10px; font-weight: 600; padding: 10px 24px;
    width: 100%;
  }
  .stButton > button:hover { opacity: 0.85; }

  /* Selectbox / input */
  .stSelectbox > div, .stTextInput > div > div {
    background: #171c27; border: 1px solid #222838;
    border-radius: 10px; color: #eef0f6;
  }

  /* Radio */
  .stRadio > label { color: #7b82a0; }

  /* Section headers */
  .section-head {
    font-size: 13px; font-weight: 600;
    color: #7b82a0; text-transform: uppercase;
    letter-spacing: .6px; margin-bottom: 8px;
  }

  /* Rec card */
  .rec-card {
    background: linear-gradient(135deg,rgba(78,159,255,.12),rgba(78,159,255,.04));
    border: 1px solid rgba(78,159,255,.3);
    border-radius: 14px; padding: 16px 18px; margin-bottom: 12px;
  }
  .rec-head { font-size:11px; font-weight:700; color:#4e9fff;
               text-transform:uppercase; letter-spacing:.6px; }
  .rec-action { font-size:15px; font-weight:600; margin:6px 0 4px; }
  .rec-reason { font-size:12px; color:#7b82a0; }

  /* Pipeline row */
  .pipe-row {
    display:flex; align-items:center; gap:14px;
    background:#171c27; border:1px solid #222838;
    border-radius:0; padding:12px 16px;
  }
  .pipe-row:first-child { border-radius:14px 14px 0 0; }
  .pipe-row:last-child  { border-radius:0 0 14px 14px; }

  /* Weather card */
  .weather-card {
    background: #171c27; border: 1px solid #222838;
    border-radius: 14px; padding: 16px;
  }

  /* Road status badge */
  .badge-free     { background:rgba(52,212,122,.15); color:#34d47a; padding:3px 10px; border-radius:6px; font-weight:600; font-size:12px; }
  .badge-slow     { background:rgba(245,197,66,.15);  color:#f5c542; padding:3px 10px; border-radius:6px; font-weight:600; font-size:12px; }
  .badge-heavy    { background:rgba(245,133,66,.15);  color:#f58542; padding:3px 10px; border-radius:6px; font-weight:600; font-size:12px; }
  .badge-jammed   { background:rgba(245,66,66,.15);   color:#f54242; padding:3px 10px; border-radius:6px; font-weight:600; font-size:12px; }

  /* Hide Streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DATA ENGINE
# ══════════════════════════════════════════════════════════════════════════════

# Base road data — NH-48 corridor, Delhi
BASE_ROADS = [
    {"id":"nh48-west",  "name":"NH-48 West Bypass", "sensor":"Loop detector",     "base_speed":72, "base_vol":1240, "coords":[[28.609,77.068],[28.615,77.110]]},
    {"id":"ring-road",  "name":"Ring Road North",    "sensor":"Camera",            "base_speed":48, "base_vol":2080, "coords":[[28.615,77.110],[28.637,77.164]]},
    {"id":"mg-road",    "name":"MG Road Junction",   "sensor":"Radar",             "base_speed":28, "base_vol":3120, "coords":[[28.637,77.164],[28.649,77.218]]},
    {"id":"toll-plaza", "name":"NH-48 Toll Plaza 3", "sensor":"LiDAR",             "base_speed":11, "base_vol":3890, "coords":[[28.649,77.218],[28.655,77.270]]},
    {"id":"nh48-east",  "name":"NH-48 East Express", "sensor":"GPS probe vehicle", "base_speed":68, "base_vol":980,  "coords":[[28.655,77.270],[28.657,77.318]]},
]

HORIZON_FACTOR = {
    "Right now":  (1.00, 1.00),
    "+15 min":    (0.80, 1.30),
    "+30 min":    (0.62, 1.55),
    "+1 hour":    (1.04, 0.80),
}

STATUS_COLOR = {
    "Free":   {"hex":"#34d47a", "badge":"badge-free"},
    "Slow":   {"hex":"#f5c542", "badge":"badge-slow"},
    "Heavy":  {"hex":"#f58542", "badge":"badge-heavy"},
    "Jammed": {"hex":"#f54242", "badge":"badge-jammed"},
}

def speed_to_status(speed):
    if speed >= 55: return "Free"
    if speed >= 35: return "Slow"
    if speed >= 18: return "Heavy"
    return "Jammed"

def get_live_roads(horizon="Right now"):
    sf, vf = HORIZON_FACTOR[horizon]
    roads = []
    for r in BASE_ROADS:
        # Add small random fluctuation
        noise = random.uniform(-3, 3)
        speed = max(4, min(85, round(r["base_speed"] * sf + noise)))
        vol   = max(200, round(r["base_vol"] * vf + random.randint(-50, 50)))
        status = speed_to_status(speed)
        roads.append({**r, "speed": speed, "volume": vol, "status": status})
    return roads

def get_summary(roads):
    speeds    = [r["speed"]  for r in roads]
    avg_speed = round(sum(speeds) / len(speeds))
    ci        = round(max(0, min(10, 10 - (avg_speed / 85 * 10))), 1)
    worst     = min(roads, key=lambda r: r["speed"])
    free_count = sum(1 for r in roads if r["status"] == "Free")
    cong_count = len(roads) - free_count
    return {"avg_speed": avg_speed, "ci": ci, "worst": worst,
            "free": free_count, "congested": cong_count}


# ══════════════════════════════════════════════════════════════════════════════
# WEATHER  — Open-Meteo (free, no key)
# ══════════════════════════════════════════════════════════════════════════════

WMO_DESC = {
    0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",
    45:"Foggy",48:"Icy fog",51:"Light drizzle",53:"Drizzle",55:"Heavy drizzle",
    61:"Light rain",63:"Rain",65:"Heavy rain",71:"Light snow",73:"Snow",
    75:"Heavy snow",80:"Rain showers",81:"Showers",82:"Heavy showers",
    95:"Thunderstorm",96:"Thunderstorm",99:"Thunderstorm"
}
WMO_ICON = {
    0:"☀️",1:"🌤",2:"⛅",3:"☁️",45:"🌫",48:"🌫",
    51:"🌦",53:"🌦",55:"🌧",61:"🌦",63:"🌧",65:"🌧",
    71:"🌨",73:"❄️",75:"❄️",80:"🌦",81:"🌧",82:"🌧",
    95:"⛈",96:"⛈",99:"⛈"
}

@st.cache_data(ttl=600)  # cache 10 minutes
def fetch_weather(lat=28.635, lon=77.224):
    try:
        url = (f"https://api.open-meteo.com/v1/forecast"
               f"?latitude={lat}&longitude={lon}"
               f"&current=temperature_2m,relative_humidity_2m,"
               f"wind_speed_10m,precipitation,weather_code,visibility"
               f"&wind_speed_unit=kmh&timezone=auto")
        r = requests.get(url, timeout=5)
        c = r.json()["current"]
        code = c["weather_code"]
        return {
            "temp":     round(c["temperature_2m"]),
            "humidity": c["relative_humidity_2m"],
            "wind":     round(c["wind_speed_10m"]),
            "rain":     round(c.get("precipitation", 0), 1),
            "vis":      round(c.get("visibility", 10000) / 1000, 1),
            "icon":     WMO_ICON.get(code, "🌡"),
            "desc":     WMO_DESC.get(code, "Unknown"),
            "code":     code,
        }
    except Exception:
        return {"temp":28,"humidity":62,"wind":14,"rain":0,"vis":10,
                "icon":"⛅","desc":"Partly cloudy (cached)","code":2}

def weather_impact(w):
    code, wind, rain = w["code"], w["wind"], w["rain"]
    if code >= 95:            return ("🚨","Severe weather — major delays likely","High Impact","#f54242")
    if code >= 61 or rain>2:  return ("🌧","Rain slowing traffic — speeds reduced 15–25%","Moderate","#f58542")
    if code >= 51 or rain>.5: return ("🌦","Light rain — minor slowdowns expected","Low Impact","#f5c542")
    if code >= 45:            return ("🌫","Fog — reduced visibility, slow down","Moderate","#f58542")
    if wind > 50:             return ("💨","Strong winds — high-sided vehicles restricted","Low Impact","#f5c542")
    return                           ("✅","No weather impact on traffic","No Impact","#34d47a")


# ══════════════════════════════════════════════════════════════════════════════
# SPEED HISTORY (simulated for chart)
# ══════════════════════════════════════════════════════════════════════════════

def get_speed_history():
    now    = datetime.now()
    times  = [now - timedelta(minutes=(23-i)*5) for i in range(24)]
    speeds = [72,71,70,68,65,60,54,48,42,36,30,26,22,19,17,15,13,12,11,13,16,20,25,34]
    speeds = [max(4, min(85, s + round(random.uniform(-2,2)))) for s in speeds]
    return pd.DataFrame({"Time": times, "Speed (km/h)": speeds})


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🚦 TrafficIQ")
    st.caption("Congestion Prediction System")
    st.divider()

    forecast = st.radio(
        "📅 Forecast Window",
        ["Right now", "+15 min", "+30 min", "+1 hour"],
        index=0
    )
    st.divider()

    st.markdown("**⚙️ ML Model**")
    st.caption("XGBoost + LSTM")
    st.progress(0.91, text="Accuracy: 91%")

    st.divider()
    st.markdown("**📡 Sensor Network**")
    col_a, col_b = st.columns(2)
    col_a.metric("Active",  "142", delta=None)
    col_b.metric("Offline", "3",   delta=None)

    st.divider()
    now_str = datetime.now().strftime("%H:%M:%S")
    st.caption(f"🕐 Last refresh: {now_str}")

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# LIVE DATA
# ══════════════════════════════════════════════════════════════════════════════

roads   = get_live_roads(forecast)
summary = get_summary(roads)
weather = fetch_weather()
w_icon, w_impact_label, w_badge, w_color = weather_impact(weather)


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(
    f"<h1 style='color:#eef0f6;margin-bottom:4px'>🚦 TrafficIQ</h1>"
    f"<p style='color:#7b82a0;margin-top:0'>Live congestion prediction · NH-48 Corridor, Delhi &nbsp;·&nbsp; "
    f"<span style='color:#34d47a;font-weight:600'>● Live</span> &nbsp;·&nbsp; {datetime.now().strftime('%H:%M:%S')}</p>",
    unsafe_allow_html=True
)

# ── TOP KPI METRICS ───────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

ci_color = "#34d47a" if summary["ci"]<4 else "#f5c542" if summary["ci"]<6 else "#f58542" if summary["ci"]<8 else "#f54242"
c1.metric("🚗 Avg Speed",        f"{summary['avg_speed']} km/h", delta=f"{summary['avg_speed']-60} from baseline", delta_color="normal")
c2.metric("📊 Congestion Index", f"{summary['ci']} / 10",        delta=f"{summary['congested']} roads congested",  delta_color="inverse")
c3.metric("📡 Active Sensors",   "142",                          delta="-3 offline",                               delta_color="off")
c4.metric("🎯 Model Accuracy",   "91%",                          delta="+2% this week",                           delta_color="normal")

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════

tab_ov, tab_roads, tab_map, tab_route, tab_pipe = st.tabs([
    "📊 Overview", "🛣️ Roads", "🗺️ Map", "🔍 Route", "⚙️ Pipeline"
])


# ═════════════════════════════════
# TAB 1 — OVERVIEW
# ═════════════════════════════════
with tab_ov:

    # Recommendation card
    worst      = summary["worst"]
    rec_msgs   = {
        "Right now": f"Avoid **{worst['name']}** for the next 30 minutes. Use Ring Road instead.",
        "+15 min":   "Leave now if you can — congestion is spreading to most roads.",
        "+30 min":   "Wait it out or take Ring Road. Peak hour in 30 minutes.",
        "+1 hour":   "If you can wait 1 hour, traffic will clear significantly.",
    }
    st.markdown(f"""
    <div class="rec-card">
      <div class="rec-head">💡 What you should do</div>
      <div class="rec-action">{rec_msgs[forecast]}</div>
      <div class="rec-reason">
        Worst road: <b>{worst['name']}</b> at <b style="color:#f54242">{worst['speed']} km/h</b>
        &nbsp;·&nbsp; Updated at {datetime.now().strftime('%H:%M:%S')}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Alert banner
    alert_time = (datetime.now() + timedelta(minutes=12)).strftime("%I:%M %p")
    clear_time = (datetime.now() + timedelta(minutes=40)).strftime("%I:%M %p")
    st.warning(
        f"⚠️ **Heavy congestion ahead** — NH-48, near Toll Plaza 3. "
        f"Expect 18-min delay. Starts at **{alert_time}**, clears by **{clear_time}**."
    )

    col_left, col_right = st.columns([1, 1])

    with col_left:
        # Congestion gauge
        st.markdown('<div class="section-head">Congestion Level</div>', unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=summary["ci"],
            delta={"reference": 5, "increasing":{"color":"#f54242"}, "decreasing":{"color":"#34d47a"}},
            number={"font":{"color":ci_color, "size":48}, "suffix":"/10"},
            gauge={
                "axis":{"range":[0,10],"tickcolor":"#7b82a0","tickfont":{"color":"#7b82a0"}},
                "bar":{"color":ci_color,"thickness":.25},
                "bgcolor":"#171c27",
                "bordercolor":"#222838",
                "steps":[
                    {"range":[0,3],  "color":"rgba(52,212,122,.1)"},
                    {"range":[3,6],  "color":"rgba(245,197,66,.1)"},
                    {"range":[6,8],  "color":"rgba(245,133,66,.1)"},
                    {"range":[8,10], "color":"rgba(245,66,66,.1)"},
                ],
                "threshold":{"line":{"color":ci_color,"width":3},"thickness":.75,"value":summary["ci"]}
            }
        ))
        fig_gauge.update_layout(
            height=260, margin=dict(l=20,r=20,t=20,b=20),
            paper_bgcolor="#0e1117", font_color="#eef0f6"
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Sentence summary
        sent_map = {
            "Right now": f"Traffic is **moderately heavy** across **{summary['congested']} roads** — {summary['free']} are moving freely.",
            "+15 min":   f"Traffic is **getting worse** — **{summary['congested']+1} roads** will be congested in 15 minutes.",
            "+30 min":   f"Traffic will be at its **worst** — expect heavy delays on most roads.",
            "+1 hour":   f"Traffic should **improve significantly** in 1 hour — most roads will be clear.",
        }
        st.info(sent_map[forecast])

    with col_right:
        # Speed trend chart
        st.markdown('<div class="section-head">Speed Trend — NH-48 (2h)</div>', unsafe_allow_html=True)
        hist = get_speed_history()
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=hist["Time"], y=hist["Speed (km/h)"],
            mode="lines", name="Speed",
            line=dict(color="#4e9fff", width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(78,159,255,.08)"
        ))
        fig_line.update_layout(
            height=260, margin=dict(l=10,r=10,t=10,b=10),
            paper_bgcolor="#0e1117", plot_bgcolor="#171c27",
            xaxis=dict(showgrid=False, tickfont=dict(color="#7b82a0"), tickformat="%H:%M"),
            yaxis=dict(gridcolor="#222838", tickfont=dict(color="#7b82a0"), range=[0,85]),
            showlegend=False
        )
        peak = hist["Speed (km/h)"].max()
        low  = hist["Speed (km/h)"].min()
        now_spd = hist["Speed (km/h)"].iloc[-1]
        st.plotly_chart(fig_line, use_container_width=True)

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Peak",  f"{peak} km/h")
        mc2.metric("Min",   f"{low} km/h")
        mc3.metric("Now",   f"{now_spd} km/h")

    st.divider()

    # Weather widget
    st.markdown('<div class="section-head">🌤 Weather · Traffic Impact</div>', unsafe_allow_html=True)
    wc1, wc2, wc3, wc4 = st.columns(4)
    wc1.metric(f"{weather['icon']} Temperature", f"{weather['temp']}°C")
    wc2.metric("💨 Wind",      f"{weather['wind']} km/h")
    wc3.metric("💧 Humidity",  f"{weather['humidity']}%")
    wc4.metric("🌧 Rain (1h)", f"{weather['rain']} mm")
    st.markdown(
        f"<div style='background:rgba(78,159,255,.06);border:1px solid rgba(78,159,255,.2);"
        f"border-radius:10px;padding:10px 16px;font-size:13px;margin-top:8px'>"
        f"{w_icon} <b style='color:{w_color}'>{w_impact_label}</b> &nbsp;·&nbsp; "
        f"<span style='color:#7b82a0'>{weather['desc']} · Visibility {weather['vis']} km</span>"
        f"&nbsp;&nbsp;<span style='background:rgba(78,159,255,.1);color:{w_color};"
        f"padding:2px 10px;border-radius:5px;font-size:11px;font-weight:700'>{w_badge}</span>"
        f"</div>",
        unsafe_allow_html=True
    )


# ═════════════════════════════════
# TAB 2 — ROADS
# ═════════════════════════════════
with tab_roads:

    st.markdown('<div class="section-head">Live Segment Predictions</div>', unsafe_allow_html=True)

    # Worst road highlight
    worst = summary["worst"]
    st.error(
        f"🔴 **Worst road:** {worst['name']} — **{worst['speed']} km/h** "
        f"({worst['volume']:,} veh/hr) · {worst['status']}"
    )

    # Road cards
    for r in roads:
        c = STATUS_COLOR[r["status"]]
        trend_delta = round(r["speed"] - r["base_speed"])
        trend_str   = f"↑ +{trend_delta}" if trend_delta > 0 else f"↓ {trend_delta}"
        trend_color = "#34d47a" if trend_delta > 0 else "#f54242" if trend_delta < -3 else "#7b82a0"

        with st.container():
            rc1, rc2, rc3, rc4 = st.columns([4, 2, 2, 2])
            rc1.markdown(
                f"<b style='font-size:14px'>{r['name']}</b><br>"
                f"<span style='font-size:12px;color:#7b82a0'>{r['sensor']} &nbsp;·&nbsp; {r['volume']:,} veh/hr</span>",
                unsafe_allow_html=True
            )
            rc2.metric("Speed", f"{r['speed']} km/h", delta=f"{trend_str} km/h", delta_color="normal" if trend_delta>=0 else "inverse")
            rc3.markdown(
                f"<div style='margin-top:12px'>"
                f"<span class='{c['badge']}'>{r['status']}</span></div>",
                unsafe_allow_html=True
            )
            rc4.markdown(
                f"<div style='margin-top:14px;font-size:12px;color:{trend_color};font-weight:600'>"
                f"{'↑ Improving' if trend_delta>3 else '↓ Worsening' if trend_delta<-3 else '→ Steady'}</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div style='height:3px;background:linear-gradient(90deg,{c['hex']} {min(100,r['speed'])}%,#222838 0%);border-radius:2px;margin-bottom:12px'></div>",
                unsafe_allow_html=True
            )

    st.divider()

    # Comparison bar chart
    st.markdown('<div class="section-head">Speed Comparison</div>', unsafe_allow_html=True)
    df_roads = pd.DataFrame([{
        "Road":   r["name"].replace("NH-48 ", "").replace(" Bypass","").replace(" Junction",""),
        "Speed":  r["speed"],
        "Status": r["status"],
        "Color":  STATUS_COLOR[r["status"]]["hex"]
    } for r in roads])

    fig_bar = go.Figure(go.Bar(
        x=df_roads["Road"], y=df_roads["Speed"],
        marker_color=df_roads["Color"],
        text=df_roads["Speed"].astype(str) + " km/h",
        textposition="outside", textfont=dict(color="#eef0f6", size=12)
    ))
    fig_bar.add_hline(y=60, line_dash="dash", line_color="#7b82a0",
                      annotation_text="Free-flow baseline (60 km/h)",
                      annotation_font_color="#7b82a0")
    fig_bar.update_layout(
        height=300, margin=dict(l=10,r=10,t=20,b=10),
        paper_bgcolor="#0e1117", plot_bgcolor="#171c27",
        xaxis=dict(tickfont=dict(color="#7b82a0"), gridcolor="#222838"),
        yaxis=dict(tickfont=dict(color="#7b82a0"), gridcolor="#222838", range=[0,90]),
        showlegend=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)


# ═════════════════════════════════
# TAB 3 — MAP
# ═════════════════════════════════
with tab_map:

    st.markdown('<div class="section-head">Live Road Map · NH-48 Corridor, Delhi</div>', unsafe_allow_html=True)

    # Build Folium dark map
    m = folium.Map(
        location=[28.633, 77.193],
        zoom_start=13,
        tiles="CartoDB dark_matter",
        prefer_canvas=True
    )

    for r in roads:
        color = STATUS_COLOR[r["status"]]["hex"]
        # Glow shadow
        folium.PolyLine(
            r["coords"], color=color, weight=14, opacity=0.15,
            tooltip=r["name"]
        ).add_to(m)
        # Main road line
        folium.PolyLine(
            r["coords"], color=color, weight=6, opacity=0.9,
            tooltip=f"{r['name']} — {r['speed']} km/h · {r['status']}"
        ).add_to(m)

        # Popup on midpoint
        mid = r["coords"][len(r["coords"])//2]
        folium.CircleMarker(
            location=mid,
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            popup=folium.Popup(
                f"<b>{r['name']}</b><br>"
                f"Speed: <b style='color:{color}'>{r['speed']} km/h</b><br>"
                f"Volume: {r['volume']:,} veh/hr<br>"
                f"Status: <b>{r['status']}</b><br>"
                f"Sensor: {r['sensor']}",
                max_width=200
            )
        ).add_to(m)

    # Pulsing marker on worst spot
    worst_mid = worst["coords"][len(worst["coords"])//2]
    folium.Marker(
        location=worst_mid,
        icon=folium.DivIcon(html="""
            <div style="width:20px;height:20px;border-radius:50%;
                        background:#f54242;border:3px solid #fff;
                        box-shadow:0 0 0 6px rgba(245,66,66,.3);">
            </div>""", icon_size=(20,20), icon_anchor=(10,10)),
        tooltip="⚠️ Worst congestion point"
    ).add_to(m)

    # Legend
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;
                background:#1e2435;border:1px solid #222838;
                border-radius:10px;padding:12px 16px;font-size:12px;
                color:#eef0f6;z-index:1000">
        <b style="color:#7b82a0">CONGESTION</b><br><br>
        <span style="color:#34d47a">━━</span> Free &nbsp;
        <span style="color:#f5c542">━━</span> Slow &nbsp;
        <span style="color:#f58542">━━</span> Heavy &nbsp;
        <span style="color:#f54242">━━</span> Jammed
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, use_container_width=True, height=450)

    st.caption("🗺️ Tap any road or marker for live details · Colors update with forecast window")


# ═════════════════════════════════
# TAB 4 — ROUTE SEARCH
# ═════════════════════════════════
with tab_route:

    st.markdown('<div class="section-head">🔍 Plan Your Route · Live Traffic Applied</div>', unsafe_allow_html=True)

    KNOWN_PLACES = [
        "NH-48 West Bypass",
        "Ring Road North",
        "MG Road Junction",
        "NH-48 Toll Plaza 3",
        "NH-48 East Express",
        "Connaught Place, New Delhi",
        "IGI Airport Terminal 3",
        "Cyber City, Gurugram",
        "Dwarka Sector 21",
        "India Gate, New Delhi",
        "Dhaula Kuan",
        "Rajiv Chowk Metro",
    ]

    PLACE_COORDS = {
        "NH-48 West Bypass":      (28.612, 77.088),
        "Ring Road North":         (28.626, 77.142),
        "MG Road Junction":        (28.646, 77.200),
        "NH-48 Toll Plaza 3":      (28.652, 77.270),
        "NH-48 East Express":      (28.656, 77.308),
        "Connaught Place, New Delhi": (28.6315, 77.2167),
        "IGI Airport Terminal 3":  (28.5562, 77.1000),
        "Cyber City, Gurugram":    (28.4949, 77.0877),
        "Dwarka Sector 21":        (28.5529, 77.0588),
        "India Gate, New Delhi":   (28.6129, 77.2295),
        "Dhaula Kuan":             (28.5934, 77.1699),
        "Rajiv Chowk Metro":       (28.6328, 77.2197),
    }

    r1, r2 = st.columns(2)
    with r1:
        from_place = st.selectbox("🟢 Starting point", KNOWN_PLACES, index=0)
    with r2:
        to_place   = st.selectbox("🔴 Destination",    KNOWN_PLACES, index=3)

    if st.button("🚗 Get Route with Live Traffic", use_container_width=True):
        if from_place == to_place:
            st.warning("Please select different starting point and destination.")
        else:
            # Haversine distance
            import math
            lat1,lon1 = PLACE_COORDS[from_place]
            lat2,lon2 = PLACE_COORDS[to_place]
            R = 6371
            dlat = math.radians(lat2-lat1)
            dlon = math.radians(lon2-lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
            dist_km = round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)), 1)

            # Travel time with traffic multiplier
            avg_spd = summary["avg_speed"]
            t_mult  = {"Free":1.0,"Slow":1.2,"Heavy":1.55,"Jammed":2.1}[worst["status"]]
            base_time = round((dist_km / avg_spd) * 60) + 5
            total_time = round(base_time * t_mult)
            eta = (datetime.now() + timedelta(minutes=total_time)).strftime("%I:%M %p")

            status_map = {
                "Free":   ("#34d47a","Good conditions"),
                "Slow":   ("#f5c542","Minor delays"),
                "Heavy":  ("#f58542","Heavy traffic"),
                "Jammed": ("#f54242","Severe delays"),
            }
            s_color, s_label = status_map[worst["status"]]

            # Summary row
            st.markdown("<br>", unsafe_allow_html=True)
            rm1, rm2, rm3, rm4 = st.columns(4)
            rm1.metric("⏱️ Est. Time",  f"{total_time} min",  delta=f"+{total_time-base_time} traffic delay", delta_color="inverse")
            rm2.metric("📍 Distance",   f"{dist_km} km")
            rm3.metric("🏁 ETA",        eta)
            rm4.metric("🚦 Conditions", s_label)

            st.markdown(
                f"<div style='background:rgba(78,159,255,.06);border:1px solid #222838;"
                f"border-radius:12px;padding:14px 18px;margin:12px 0'>"
                f"<b>🟢 From:</b> {from_place} &nbsp;→&nbsp; <b>🔴 To:</b> {to_place}<br>"
                f"<span style='color:#7b82a0;font-size:12px'>"
                f"Via NH-48 corridor · Live traffic applied · Forecast: {forecast}</span></div>",
                unsafe_allow_html=True
            )

            # Turn-by-turn steps
            st.markdown('<div class="section-head" style="margin-top:8px">Turn-by-turn steps</div>', unsafe_allow_html=True)
            steps = [{"Road":"Depart","Detail":from_place,"Status":"Free"}] + \
                    [{"Road":r["name"],"Detail":f"{r['speed']} km/h · {r['volume']:,} veh/hr","Status":r["status"]} for r in roads] + \
                    [{"Road":"Arrive","Detail":f"{to_place} · ETA {eta}","Status":"Free"}]

            df_steps = pd.DataFrame(steps)
            df_steps["Color"] = df_steps["Status"].map(lambda s: STATUS_COLOR.get(s,STATUS_COLOR["Free"])["hex"])

            for i, step in df_steps.iterrows():
                c = STATUS_COLOR.get(step["Status"], STATUS_COLOR["Free"])
                dot = "🟢" if i==0 else "🔴" if i==len(df_steps)-1 else "⚫"
                badge = f"<span class='{c['badge']}'>{step['Status']}</span>" if 0<i<len(df_steps)-1 else ""
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:12px;"
                    f"padding:10px 14px;background:#171c27;"
                    f"border-left:3px solid {c['hex']};"
                    f"border-bottom:1px solid #222838;"
                    f"{'border-radius:12px 12px 0 0' if i==0 else 'border-radius:0 0 12px 12px' if i==len(df_steps)-1 else ''}'>"
                    f"<span style='font-size:16px'>{dot}</span>"
                    f"<div style='flex:1'><b>{step['Road']}</b><br>"
                    f"<span style='font-size:12px;color:#7b82a0'>{step['Detail']}</span></div>"
                    f"{badge}</div>",
                    unsafe_allow_html=True
                )

            # Route map
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-head">Route on Map</div>', unsafe_allow_html=True)
            rm = folium.Map(location=[(lat1+lat2)/2,(lon1+lon2)/2], zoom_start=12, tiles="CartoDB dark_matter")

            # Road overlays
            for r in roads:
                color = STATUS_COLOR[r["status"]]["hex"]
                folium.PolyLine(r["coords"], color=color, weight=5, opacity=0.8,
                                tooltip=f"{r['name']} — {r['speed']} km/h").add_to(rm)

            # Route line
            route_pts = [[lat1,lon1]] + [r["coords"][len(r["coords"])//2] for r in roads] + [[lat2,lon2]]
            folium.PolyLine(route_pts, color="#4e9fff", weight=4, opacity=0.7,
                            dash_array="10 6").add_to(rm)

            # Start / end markers
            folium.Marker([lat1,lon1], icon=folium.DivIcon(
                html='<div style="width:14px;height:14px;border-radius:50%;background:#34d47a;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.4)"></div>',
                icon_size=(14,14), icon_anchor=(7,7)), tooltip=f"🟢 {from_place}").add_to(rm)
            folium.Marker([lat2,lon2], icon=folium.DivIcon(
                html='<div style="width:14px;height:14px;border-radius:50%;background:#f54242;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.4)"></div>',
                icon_size=(14,14), icon_anchor=(7,7)), tooltip=f"🔴 {to_place}").add_to(rm)

            st_folium(rm, use_container_width=True, height=350)


# ═════════════════════════════════
# TAB 5 — PIPELINE
# ═════════════════════════════════
with tab_pipe:

    st.markdown('<div class="section-head">ML Inference Pipeline · Current Cycle</div>', unsafe_allow_html=True)
    st.caption("This panel shows the internal data flow from sensors to prediction output.")

    pipeline_stages = [
        ("📡", "Traffic Sensors",     "142 sensors collecting real-time speed & volume",       "✅ Live",     "#34d47a", 1.00),
        ("🗄️", "Historical Data",     "18 months of traffic patterns loaded into model",       "✅ Ready",    "#34d47a", 1.00),
        ("⚙️", "Feature Engineering","34 features extracted: time, weather, volume, day-type", "✅ Done",     "#34d47a", 1.00),
        ("🤖", "ML Model",            "XGBoost + LSTM running inference on current features",   "🔄 Running",  "#4e9fff", 0.65),
        ("📊", "Congestion Output",   "Predictions pushed to dashboard every 30 seconds",      "⏳ Waiting",  "#7b82a0", 0.20),
    ]

    for icon, name, detail, status, color, progress in pipeline_stages:
        pc1, pc2, pc3 = st.columns([1, 5, 2])
        pc1.markdown(f"<div style='font-size:24px;text-align:center;padding-top:8px'>{icon}</div>", unsafe_allow_html=True)
        with pc2:
            st.markdown(f"**{name}**")
            st.caption(detail)
            st.progress(progress)
        pc3.markdown(
            f"<div style='text-align:right;padding-top:12px;"
            f"font-weight:600;color:{color}'>{status}</div>",
            unsafe_allow_html=True
        )
        st.divider()

    # Model performance metrics
    st.markdown('<div class="section-head">Model Performance</div>', unsafe_allow_html=True)
    mp1, mp2, mp3, mp4 = st.columns(4)
    mp1.metric("Accuracy",  "91.3%",  delta="+2.1%")
    mp2.metric("Precision", "89.7%",  delta="+1.4%")
    mp3.metric("Recall",    "92.1%",  delta="+0.8%")
    mp4.metric("F1 Score",  "90.9%",  delta="+1.2%")

    # Feature importance chart
    st.markdown('<div class="section-head" style="margin-top:16px">Top Feature Importances</div>', unsafe_allow_html=True)
    features = pd.DataFrame({
        "Feature":    ["Time of day","Vehicle volume","Day of week","Weather code","Upstream speed","Wind speed","Historical avg","Incident count","Visibility","Rain (1h)"],
        "Importance": [0.28, 0.22, 0.14, 0.10, 0.08, 0.06, 0.05, 0.04, 0.02, 0.01]
    }).sort_values("Importance")

    fig_feat = go.Figure(go.Bar(
        x=features["Importance"], y=features["Feature"],
        orientation="h",
        marker_color="#4e9fff",
        text=[f"{v:.0%}" for v in features["Importance"]],
        textposition="outside",
        textfont=dict(color="#eef0f6", size=11)
    ))
    fig_feat.update_layout(
        height=320, margin=dict(l=10,r=60,t=10,b=10),
        paper_bgcolor="#0e1117", plot_bgcolor="#171c27",
        xaxis=dict(gridcolor="#222838", tickfont=dict(color="#7b82a0"), tickformat=".0%"),
        yaxis=dict(tickfont=dict(color="#eef0f6")),
        showlegend=False
    )
    st.plotly_chart(fig_feat, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown(
    "<div style='text-align:center;color:#7b82a0;font-size:12px'>"
    "🚦 TrafficIQ · NH-48 Corridor, Delhi &nbsp;·&nbsp; "
    "XGBoost + LSTM ML Model &nbsp;·&nbsp; "
    "Open-Meteo Weather &nbsp;·&nbsp; OpenStreetMap &nbsp;·&nbsp; "
    f"Last updated {datetime.now().strftime('%H:%M:%S')}"
    "</div>",
    unsafe_allow_html=True
)

import os
import json
import time
from datetime import datetime
import streamlit as st
import pandas as pd
import textwrap
import pydeck as pdk
import requests
import folium
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from modules.auth_session import get_authenticated_user
from modules.road_status_provider import get_authoritative_corridor_status, get_static_fallback_corridors

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
_HELP_REQUESTS_FILE = os.path.join(_DATA_DIR, "public_help_requests.json")

def _load_public_help_requests():
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.exists(_HELP_REQUESTS_FILE):
        return []
    try:
        with open(_HELP_REQUESTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def _save_public_help_request(report):
    os.makedirs(_DATA_DIR, exist_ok=True)
    current = _load_public_help_requests()
    current.append(report)
    temp_file = _HELP_REQUESTS_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        os.replace(temp_file, _HELP_REQUESTS_FILE)
    except Exception:
        try:
            with open(_HELP_REQUESTS_FILE, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2)
        except Exception:
            pass


def h(html_str):
    return textwrap.dedent(html_str).strip()

@st.cache_data(ttl=60)
def fetch_live_weather(lat=26.1445, lon=91.7362):
    """Fetches real live regional weather telemetry from Open-Meteo API."""
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code"
        )
        response = requests.get(url, timeout=4)
        if response.status_code == 200:
            curr = response.json().get("current", {})
            return {
                "temperature": curr.get("temperature_2m", 28.0),
                "humidity": curr.get("relative_humidity_2m", 88),
                "rainfall": curr.get("precipitation", 0.0),
                "wind": curr.get("wind_speed_10m", 12.0),
                "weather_code": curr.get("weather_code", 0),
                "is_live": True
            }
    except Exception:
        pass
    return {
        "temperature": 28.0,
        "humidity": 88,
        "rainfall": 0.0,
        "wind": 12.0,
        "weather_code": 0,
        "is_live": False
    }

def render_overview_page(dashboard_img_b64, T, language, localize_number):
    """
    Renders the post-login Command Center Overview matching Screen 2 from user mockup:
    - Left: 8 Interactive feature tiles with icons (clicking any tile navigates to that page)
    - Center: Glowing GIS Map of North East India with live logistics network
    - Right: Live Telemetry (Weather, KPI counters, and Road Blockage alert)
    - Bottom: Role-based Command Center (Field Officer vs General User) and Integrated Logistics banner
    """

    auth_user = st.session_state.get("authenticated_user") or get_authenticated_user()
    user_role = auth_user.get("role") if auth_user else st.session_state.get("user_role", "Field Officer")

    # Current GIS Mode Selection (Persisted in session state)
    gis_mode = st.session_state.get("home_gis_mode", "Live GIS")
    if gis_mode == "Simulation":
        gis_mode = "Live GIS"
        st.session_state["home_gis_mode"] = "Live GIS"

    # 3-Column Command Center Grid
    c_left, c_center, c_right = st.columns([1.05, 2.05, 1.1])

    # ==========================================
    # LEFT COLUMN: Supply & Cargo Real-Time Panel
    # ==========================================
    with c_left:
        gps_active = ("real_gps_coord" in st.session_state and st.session_state["real_gps_coord"].get("lat") is not None)

        if gis_mode == "Live GIS":
            headline_val = "4 Active"
            headline_sub = "2 Critical · 1 At Risk"
            chip_req = "4"
            chip_crit = "2"
            chip_active = "4"
            chip_delay = "1"
        else:
            headline_val = "Live Telemetry"
            headline_sub = "1 Live GPS" if gps_active else "Awaiting GPS"
            chip_req = "Offline"
            chip_crit = "--"
            chip_active = "1 Unit" if gps_active else "0 Units"
            chip_delay = "0"

        # 1. Top Card: Supply & Cargo Continuity Overview (matches .telemetry-weather-card visual language)
        st.markdown(h(f"""
        <div class="telemetry-weather-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase; font-weight:700;">SUPPLY & CARGO</div>
                    <div style="font-size:1.2rem; font-weight:800; color:#ffffff; font-family:'Outfit',sans-serif;">Dispatch & Feeds</div>
                </div>
                <span style="font-size:2rem;">📦</span>
            </div>
            <div style="margin-top:8px; display:flex; align-items:baseline; gap:8px;">
                <span style="font-size:1.8rem; font-weight:900; color:#c084fc; font-family:'Outfit',sans-serif;">{headline_val}</span>
                <span style="font-size:0.85rem; color:#cbd5e1;">{headline_sub}</span>
            </div>
        </div>
        """), unsafe_allow_html=True)

        # 2. KPI Metrics: Supply & Cargo Status Chips (strictly matching .telemetry-kpi-container)
        crit_dot_class = "red" if gis_mode == "Live GIS" else "yellow"
        delay_dot_class = "amber" if gis_mode == "Live GIS" else "green"
        st.markdown(h(f"""
        <div class="telemetry-kpi-container">
            <div class="telemetry-kpi-chip">
                <span class="kpi-dot" style="background:#a855f7; box-shadow:0 0 8px #a855f7;"></span>
                <span class="kpi-label">Supply Requests</span>
                <span class="kpi-val">{chip_req}</span>
            </div>
            <div class="telemetry-kpi-chip">
                <span class="kpi-dot {crit_dot_class}"></span>
                <span class="kpi-label">Critical Supplies</span>
                <span class="kpi-val">{chip_crit}</span>
            </div>
            <div class="telemetry-kpi-chip">
                <span class="kpi-dot green"></span>
                <span class="kpi-label">Active Shipments</span>
                <span class="kpi-val">{chip_active}</span>
            </div>
            <div class="telemetry-kpi-chip">
                <span class="kpi-dot {delay_dot_class}"></span>
                <span class="kpi-label">Delayed Shipments</span>
                <span class="kpi-val">{chip_delay}</span>
            </div>
        </div>
        """), unsafe_allow_html=True)

        # 3. Bottom Card: Priority Cargo / Telemetry Status (strictly matching .telemetry-alert-card)
        if gis_mode == "Live GIS":
            st.markdown(h("""
            <div class="telemetry-alert-card" style="border-color: rgba(168, 85, 247, 0.35);">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                    <span style="font-size:1.2rem;">🚚</span>
                    <span style="font-size:0.82rem; font-weight:800; color:#c084fc; text-transform:uppercase; letter-spacing:0.05em;">Priority Cargo</span>
                </div>
                <div style="font-size:0.92rem; font-weight:700; color:#ffffff;">V03 · Critical Medicine</div>
                <p style="margin:4px 0 6px 0; font-size:0.78rem; color:#94a3b8; line-height:1.4;">
                    Haflong NH-27 risk at 82%. Reroute recommended to maintain Imphal hospital supply continuity.
                </p>
                <div style="font-size:0.75rem; color:#cbd5e1; border-top:1px solid rgba(255,255,255,0.08); padding-top:6px; margin-bottom:6px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                        <span>V15 · Medicine → Agartala</span>
                        <span style="color:#fb923c; font-weight:700;">6h ETA</span>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <span>V07 · Food → Shillong</span>
                        <span style="color:#38bdf8; font-weight:700;">5h ETA</span>
                    </div>
                </div>
                <div style="display:inline-block; font-size:0.72rem; background:rgba(168, 85, 247, 0.2); color:#e9d5ff; padding:2px 8px; border-radius:4px; font-weight:700;">
                    SIMULATED CARGO DISPATCH
                </div>
            </div>
            """), unsafe_allow_html=True)
        else:
            gps_status_text = "Live ground device GPS active. Streaming real-time coordinates." if gps_active else "Click location button below map to acquire live GPS."
            st.markdown(h(f"""
            <div class="telemetry-alert-card" style="border-color: rgba(56, 189, 248, 0.35);">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                    <span style="font-size:1.2rem;">🛰️</span>
                    <span style="font-size:0.82rem; font-weight:800; color:#38bdf8; text-transform:uppercase; letter-spacing:0.05em;">Live Telemetry Link</span>
                </div>
                <div style="font-size:0.92rem; font-weight:700; color:#ffffff;">WMS / TMS Live Feed Offline</div>
                <p style="margin:4px 0 8px 0; font-size:0.78rem; color:#94a3b8; line-height:1.4;">
                    {gps_status_text} External logistics ERP/WMS API not configured. No simulated coordinates displayed.
                </p>
                <div style="display:inline-block; font-size:0.72rem; background:rgba(56, 189, 248, 0.2); color:#7dd3fc; padding:2px 8px; border-radius:4px; font-weight:700;">
                    LIVE GPS DATA UNAVAILABLE
                </div>
            </div>
            """), unsafe_allow_html=True)

    # ==========================================
    # CENTER COLUMN: GIS Holographic Map Preview
    # ==========================================
    with c_center:
        # Fixed geographic landmarks/nodes of the NER logistics network
        gis_locations = pd.DataFrame([
            {"name": "Guwahati Hub", "lat": 26.1445, "lon": 91.7362, "type": "Warehouse Hub"},
            {"name": "Imphal", "lat": 24.8170, "lon": 93.9368, "type": "Regional Destination"},
            {"name": "Shillong", "lat": 25.5788, "lon": 91.8933, "type": "Regional Destination"},
            {"name": "Aizawl", "lat": 23.7271, "lon": 92.7176, "type": "Regional Destination"},
            {"name": "Agartala", "lat": 23.8315, "lon": 91.2868, "type": "Regional Destination"},
            {"name": "Dimapur", "lat": 25.9000, "lon": 93.7200, "type": "Logistics Junction"},
            {"name": "Kohima", "lat": 25.6700, "lon": 94.1100, "type": "Regional Destination"},
            {"name": "Silchar", "lat": 24.8333, "lon": 92.7976, "type": "Transit Hub"},
            {"name": "Tezpur", "lat": 26.6300, "lon": 92.8000, "type": "Transit Node"},
            {"name": "Itanagar", "lat": 27.1000, "lon": 93.6200, "type": "Regional Destination"}
        ])

        # ============================================================
        # DATA PREPARATION BASED ON ACTIVE GIS MODE
        # ============================================================
        if gis_mode == "Live GIS":
            # Baseline simulated vehicles
            if "gis_vehicles" in st.session_state and isinstance(st.session_state.gis_vehicles, pd.DataFrame):
                gis_vehicles = st.session_state.gis_vehicles
            elif "vehicles" in st.session_state and isinstance(st.session_state.vehicles, pd.DataFrame):
                gis_vehicles = st.session_state.vehicles
            else:
                gis_vehicles = pd.DataFrame([
                    {
                        "vehicle": "V01",
                        "lat": 25.40,
                        "lon": 92.20,
                        "cargo": "Medicine",
                        "destination": "Imphal",
                        "eta": "5h 20m",
                        "status": "ON ROUTE"
                    },
                    {
                        "vehicle": "V02",
                        "lat": 25.85,
                        "lon": 91.55,
                        "cargo": "Food Supplies",
                        "destination": "Shillong",
                        "eta": "2h 45m",
                        "status": "ON ROUTE"
                    },
                    {
                        "vehicle": "V03",
                        "lat": 24.95,
                        "lon": 92.70,
                        "cargo": "Medicine",
                        "destination": "Imphal",
                        "eta": "8h 10m",
                        "status": "AT RISK"
                    }
                ])

            # Regional traffic monitoring incidents
            gis_incidents = pd.DataFrame([
                {
                    "name": "High Risk Corridor",
                    "lat": 24.95,
                    "lon": 92.70,
                    "risk": "82%",
                    "incident": "Heavy Rainfall / Hill Section Risk"
                }
            ])

            # Authoritative GIS Road-Status Data Layer (Recent / Live Real-World Conditions with Fallback)
            try:
                gis_corridors, corridor_data, _corridor_meta = get_authoritative_corridor_status()
            except Exception:
                gis_corridors, corridor_data, _corridor_meta = get_static_fallback_corridors()

            # Small unobtrusive Supply & Cargo GIS markers (Live GIS mode)
            gis_supply_cargo = pd.DataFrame([
                {
                    "name": "📦 Imphal Supply Depot",
                    "lat": 24.8170,
                    "lon": 93.9368,
                    "symbol": "📦",
                    "vehicle": "",
                    "cargo": "",
                    "status": "Stock: 14h Medicine (High Dependency)",
                    "advisory": "Disruption Risk: 82%",
                    "incident": "",
                    "color": [168, 85, 247, 230],
                    "radius": 5500
                },
                {
                    "name": "📦 Shillong Supply Depot",
                    "lat": 25.5788,
                    "lon": 91.8933,
                    "symbol": "📦",
                    "vehicle": "",
                    "cargo": "",
                    "status": "Stock: 30h Food Supplies (Medium Dependency)",
                    "advisory": "Disruption Risk: 21%",
                    "incident": "",
                    "color": [168, 85, 247, 230],
                    "radius": 5500
                },
                {
                    "name": "📦 Aizawl Supply Depot",
                    "lat": 23.7271,
                    "lon": 92.7176,
                    "symbol": "📦",
                    "vehicle": "",
                    "cargo": "",
                    "status": "Stock: 26h Construction Materials",
                    "advisory": "Disruption Risk: 38%",
                    "incident": "",
                    "color": [168, 85, 247, 230],
                    "radius": 5500
                },
                {
                    "name": "📦 Agartala Supply Depot",
                    "lat": 23.8315,
                    "lon": 91.2868,
                    "symbol": "📦",
                    "vehicle": "",
                    "cargo": "",
                    "status": "Stock: 20h Medicine (High Dependency)",
                    "advisory": "Disruption Risk: 25%",
                    "incident": "",
                    "color": [168, 85, 247, 230],
                    "radius": 5500
                },
                {
                    "name": "🚚 Cargo V03",
                    "lat": 24.95,
                    "lon": 92.70,
                    "symbol": "🚚",
                    "vehicle": "",
                    "cargo": " (Medicine → Imphal)",
                    "status": "Priority: Critical (81/100)",
                    "advisory": "ETA: 8h · Corridor Risk: 82%",
                    "incident": "",
                    "color": [192, 132, 252, 230],
                    "radius": 5500
                },
                {
                    "name": "🚚 Cargo V07",
                    "lat": 25.85,
                    "lon": 91.55,
                    "symbol": "🚚",
                    "vehicle": "",
                    "cargo": " (Food Supplies → Shillong)",
                    "status": "Priority: High (58/100)",
                    "advisory": "ETA: 5h · Corridor Risk: 21%",
                    "incident": "",
                    "color": [192, 132, 252, 230],
                    "radius": 5500
                },
                {
                    "name": "🚚 Cargo V11",
                    "lat": 24.30,
                    "lon": 92.75,
                    "symbol": "🚚",
                    "vehicle": "",
                    "cargo": " (Construction Material → Aizawl)",
                    "status": "Priority: Normal (42/100)",
                    "advisory": "ETA: 7h · Corridor Risk: 38%",
                    "incident": "",
                    "color": [192, 132, 252, 230],
                    "radius": 5500
                },
                {
                    "name": "🚚 Cargo V15",
                    "lat": 23.80,
                    "lon": 91.90,
                    "symbol": "🚚",
                    "vehicle": "",
                    "cargo": " (Medicine → Agartala)",
                    "status": "Priority: High (64/100)",
                    "advisory": "ETA: 6h · Corridor Risk: 25%",
                    "incident": "",
                    "color": [192, 132, 252, 230],
                    "radius": 5500
                }
            ])

        else:
            # ========================================================
            # REAL GPS MODE: Real available GPS & Open-Meteo live data
            # ========================================================
            # 1. Real Vehicle Coordinates
            if "real_gps_coord" in st.session_state and st.session_state["real_gps_coord"].get("lat") is not None:
                rc = st.session_state["real_gps_coord"]
                accuracy_val = round(rc.get("accuracy", 10.0))
                gis_vehicles = pd.DataFrame([{
                    "vehicle": "LIVE-GPS-01",
                    "lat": rc["lat"],
                    "lon": rc["lon"],
                    "cargo": "Real-Time Telemetry Unit",
                    "destination": "Active Transit Monitoring",
                    "eta": "Live Tracking",
                    "status": f"LIVE GPS (±{accuracy_val}m)"
                }])
            else:
                gis_vehicles = pd.DataFrame(columns=["vehicle", "lat", "lon", "cargo", "destination", "eta", "status"])

            # 2. Ground-Truth Verified Incident Reports
            submitted = st.session_state.get("submitted_reports", [])
            if submitted:
                gis_incidents = pd.DataFrame(submitted)
            else:
                gis_incidents = pd.DataFrame(columns=["name", "lat", "lon", "risk", "incident"])

            # 3. Live Supply & Cargo GPS Data (Empty if no live external API available - do not fabricate)
            gis_supply_cargo = pd.DataFrame(columns=[
                "name", "lat", "lon", "symbol", "vehicle", "cargo", "status", "advisory", "incident", "color", "radius"
            ])

            # 4. Real-Time Risk Calculation from Live Open-Meteo Weather API
            live_w = fetch_live_weather(lat=26.1445, lon=91.7362)
            rain_val = live_w.get("rainfall", 0.0)
            wind_val = live_w.get("wind", 10.0)
            base_risk = int(min(88, max(10, 14 + int(rain_val * 8) + int(max(0, wind_val - 20) * 1.5))))

            corr_specs = [
                {"name": "Corridor A (Guwahati → Shillong → Haflong → Silchar)", "short": "Corridor A (Guwahati → Shillong → Silchar)", "path": [[91.7362, 26.1445], [91.8933, 25.5788], [92.45, 25.15], [92.7976, 24.8333]], "mod": 6},
                {"name": "Corridor B (Guwahati → Tezpur → Itanagar)", "short": "Corridor B (Guwahati → Tezpur → Itanagar)", "path": [[91.7362, 26.1445], [92.80, 26.63], [93.62, 27.10]], "mod": -4},
                {"name": "Corridor C (Silchar → Imphal)", "short": "Corridor C (Silchar → Imphal)", "path": [[92.7976, 24.8333], [93.30, 24.85], [93.9368, 24.8170]], "mod": 10},
                {"name": "Corridor D (Dimapur → Kohima)", "short": "Corridor D (Dimapur → Kohima)", "path": [[93.72, 25.90], [94.11, 25.67]], "mod": 0},
                {"name": "Corridor E (Guwahati → Dimapur)", "short": "Corridor E (Guwahati → Dimapur)", "path": [[91.7362, 26.1445], [92.95, 26.10], [93.72, 25.90]], "mod": 2},
                {"name": "Corridor F (Silchar → Aizawl)", "short": "Corridor F (Silchar → Aizawl)", "path": [[92.7976, 24.8333], [92.7176, 23.7271]], "mod": 4},
                {"name": "Corridor G (Aizawl → Agartala)", "short": "Corridor G (Aizawl → Agartala)", "path": [[92.7176, 23.7271], [91.2868, 23.8315]], "mod": -2}
            ]

            map_corrs = []
            tbl_rows = []
            for cs in corr_specs:
                r_val = min(92, max(10, base_risk + cs["mod"]))
                if r_val >= 75:
                    c_status = "🔴 Blocked"
                    c_color = [239, 68, 68, 255]
                    c_width = 7
                elif r_val >= 50:
                    c_status = "🟠 At Risk"
                    c_color = [234, 179, 8, 230]
                    c_width = 5
                elif r_val >= 25:
                    c_status = "🔵 Moderate"
                    c_color = [56, 189, 248, 230]
                    c_width = 4
                else:
                    c_status = "🟢 Accessible"
                    c_color = [34, 197, 94, 230]
                    c_width = 4

                if rain_val > 0:
                    adv = f"Live Rain: {rain_val:.1f}mm/h · Speed restriction active"
                elif wind_val > 25:
                    adv = f"Live Telemetry: {wind_val:.1f}km/h crosswinds monitored"
                else:
                    adv = f"Live Telemetry: Normal clear transit window ({live_w.get('temperature', 26):.1f}°C, 0mm rain)"

                map_corrs.append({
                    "name": cs["name"],
                    "path": cs["path"],
                    "status": c_status,
                    "color": c_color,
                    "width": c_width,
                    "advisory": adv
                })

                if cs.get("short") in ["Corridor A (Guwahati → Shillong → Silchar)", "Corridor B (Guwahati → Tezpur → Itanagar)", "Corridor C (Silchar → Imphal)", "Corridor D (Dimapur → Kohima)"]:
                    tbl_rows.append({
                        "Corridor": cs["short"],
                        "Status": c_status,
                        "Risk Score": f"{r_val}%",
                        "Advisory": adv
                    })

            gis_corridors = pd.DataFrame(map_corrs)
            corridor_data = pd.DataFrame(tbl_rows)

        # ------------------------------------------------------------
        # MAP LAYERS CREATION
        # ------------------------------------------------------------
        layer_corridors = pdk.Layer(
            "PathLayer",
            data=gis_corridors,
            get_path="path",
            get_color="color",
            get_width="width",
            width_min_pixels=3,
            pickable=True
        )

        layer_locations = pdk.Layer(
            "ScatterplotLayer",
            data=gis_locations,
            get_position="[lon, lat]",
            get_radius=11000,
            get_fill_color=[56, 189, 248, 210],
            pickable=True
        )

        layer_vehicles = pdk.Layer(
            "ScatterplotLayer",
            data=gis_vehicles,
            get_position="[lon, lat]",
            get_radius=9000,
            get_fill_color=[245, 158, 11, 240],
            pickable=True
        )

        layer_incidents = pdk.Layer(
            "ScatterplotLayer",
            data=gis_incidents,
            get_position="[lon, lat]",
            get_radius=14000,
            get_fill_color=[239, 68, 68, 240],
            pickable=True
        )

        # Small unobtrusive Supply & Cargo map markers
        layer_supply_cargo_dots = pdk.Layer(
            "ScatterplotLayer",
            data=gis_supply_cargo,
            get_position="[lon, lat]",
            get_radius="radius",
            get_fill_color="color",
            get_line_color=[255, 255, 255, 180],
            line_width_min_pixels=1,
            stroked=True,
            pickable=True
        )

        layer_supply_cargo_icons = pdk.Layer(
            "TextLayer",
            data=gis_supply_cargo,
            get_position="[lon, lat]",
            get_text="symbol",
            get_size=13,
            get_color=[255, 255, 255, 255],
            get_alignment_baseline="'center'",
            get_text_anchor="'middle'",
            pickable=True
        )

        view_state = pdk.ViewState(
            latitude=25.4,
            longitude=92.8,
            zoom=5.7,
            pitch=20
        )

        deck = pdk.Deck(
            layers=[
                layer_corridors,
                layer_locations,
                layer_vehicles,
                layer_incidents,
                layer_supply_cargo_dots,
                layer_supply_cargo_icons
            ],
            initial_view_state=view_state,
            map_provider="carto",
            map_style=pdk.map_styles.CARTO_DARK,
            tooltip={
                "html": "<b>{name}</b>{vehicle} {cargo}<br/>{status} {advisory} {incident}",
                "style": {
                    "backgroundColor": "#0f172a",
                    "color": "#ffffff",
                    "border": "1px solid rgba(56, 189, 248, 0.4)",
                    "borderRadius": "6px",
                    "fontSize": "11px"
                }
            }
        )

        # Integrated Container: HUD Header (Title Badge + Embedded Road Condition Legend + Supply/Cargo Legend) + DeckGL Map
        st.markdown(h("""
        <style>
        .overview-map-hud-header {
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-bottom: none;
            border-radius: 18px 18px 0 0;
            padding: 8px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 0;
        }
        div[data-testid="stDeckGlChart"],
        div[data-testid="stDeckGlChart"] > div,
        div[data-testid="stDeckGlChart"] canvas,
        div[data-testid="stDeckGlChart"] .mapboxgl-map,
        div[data-testid="stDeckGlChart"] .maplibregl-map {
            background-color: #0b0f19 !important;
            background: #0b0f19 !important;
        }
        div[data-testid="stDeckGlChart"] {
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-top: none;
            border-radius: 0 0 18px 18px;
            overflow: hidden;
            box-shadow: 0 14px 35px -10px rgba(0, 0, 0, 0.7);
            margin-bottom: 12px;
        }
        div[data-testid="stDeckGlChart"] > div {
            border-radius: 0 0 18px 18px;
            overflow: hidden;
        }
        /* High-contrast clean white for GIS Mode radio option labels */
        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] label p,
        div[data-testid="stRadio"] label span,
        div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stRadio"] div[role="radiogroup"] label p {
            color: #FFFFFF !important;
            font-weight: 600 !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
        }
        </style>
        <div class="overview-map-hud-header">
            <div style="display:flex; align-items:center; gap:8px; font-size:0.75rem; font-weight:700; color:#38bdf8; font-family:'Outfit',sans-serif;">
                <span class="nav-pulse-dot" style="display:inline-block;"></span>
                <span>Active GIS Mesh · Real-Time Satellite & Telemetry Feeds</span>
            </div>
            <div style="display:flex; align-items:center; gap:10px; font-size:0.72rem; font-weight:600; color:#cbd5e1;">
                <span style="display:inline-flex; align-items:center; gap:4px;"><span style="color:#22c55e; font-size:0.8rem;">🟢</span> Safe</span>
                <span style="display:inline-flex; align-items:center; gap:4px;"><span style="color:#38bdf8; font-size:0.8rem;">🔵</span> Medium</span>
                <span style="display:inline-flex; align-items:center; gap:4px;"><span style="color:#eab308; font-size:0.8rem;">🟡</span> Danger</span>
                <span style="display:inline-flex; align-items:center; gap:4px;"><span style="color:#ef4444; font-size:0.8rem;">🔴</span> Road Blockage</span>
                <span style="color:#475569;">|</span>
                <span style="display:inline-flex; align-items:center; gap:3px;"><span style="font-size:0.8rem;">📦</span> Supply</span>
                <span style="display:inline-flex; align-items:center; gap:3px;"><span style="font-size:0.8rem;">🚚</span> Cargo</span>
            </div>
        </div>
        """), unsafe_allow_html=True)

        st.pydeck_chart(deck, use_container_width=True, height=410)

        # ------------------------------------------------------------
        # 1. GIS MODE CONTROL (Directly below existing GIS map)
        # ------------------------------------------------------------
        st.markdown("<div style='margin-top:4px; margin-bottom:-4px; font-size:0.75rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em;'>GIS Mode</div>", unsafe_allow_html=True)
        selected_mode = st.radio(
            "GIS Mode",
            ["Live GIS", "Real GPS"],
            index=0 if gis_mode == "Live GIS" else 1,
            horizontal=True,
            key="home_gis_mode",
            label_visibility="collapsed"
        )

        # ------------------------------------------------------------
        # 2. REAL GPS ACQUISITION / STATUS (When Real GPS is selected)
        # ------------------------------------------------------------
        if selected_mode == "Real GPS":
            gps_loc = streamlit_geolocation()
            if gps_loc and gps_loc.get("latitude") is not None:
                st.session_state["real_gps_coord"] = {
                    "lat": float(gps_loc["latitude"]),
                    "lon": float(gps_loc["longitude"]),
                    "accuracy": gps_loc.get("accuracy", 10.0)
                }
            if "real_gps_coord" in st.session_state and st.session_state["real_gps_coord"].get("lat") is not None:
                c_info = st.session_state["real_gps_coord"]
                st.caption(f"🟢 Live Device GPS Active: {c_info['lat']:.4f}°N, {c_info['lon']:.4f}°E (Accuracy: ±{c_info['accuracy']:.1f}m)")
            else:
                st.caption("📍 Live GPS source: Click the location button above to acquire real device coordinates. (If permission denied or unavailable, live GPS feed cannot be acquired).")

        # ------------------------------------------------------------
        # 3. REAL-TIME CORRIDOR TABLE (Immediately below GIS Mode control)
        # ------------------------------------------------------------
        st.dataframe(corridor_data, use_container_width=True, hide_index=True)

    # ==========================================
    # RIGHT COLUMN: Live Telemetry Panel
    # ==========================================
    with c_right:
        @st.fragment(run_every=30)
        def render_telemetry_live_panel(v_df, inc_df, corr_df, active_mode):
            # 1. Live Regional Weather from Open-Meteo API
            live_w = fetch_live_weather(lat=26.1445, lon=91.7362)
            w_code = live_w.get("weather_code", 0)
            if w_code == 0:
                w_desc = "Clear Sky"
                w_icon = "☀️"
            elif w_code in [1, 2, 3]:
                w_desc = "Partly Cloudy"
                w_icon = "⛅"
            elif w_code in [45, 48]:
                w_desc = "Fog / Mist"
                w_icon = "🌫️"
            elif w_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                w_desc = "Light Rain" if w_code in [51, 61, 80] else "Rain Showers"
                w_icon = "🌧️"
            elif w_code in [95, 96, 99]:
                w_desc = "Thunderstorm"
                w_icon = "⛈️"
            else:
                w_desc = "Overcast"
                w_icon = "☁️"

            w_temp_str = f"{round(live_w['temperature'])}°C"
            w_cond_str = f"{w_desc} · {live_w['humidity']}% Humidity"

            # 2. Dynamic Metric: Safe Roads (Corridors among A–G whose final GIS status is GREEN / SAFE)
            val_safe_roads = int(corr_df["status"].apply(
                lambda s: str(s).strip().upper() == "SAFE" or "ACCESSIBLE" in str(s).upper() or "🟢" in str(s)
            ).sum())

            # 3. Dynamic Metric: Dangerous Roads (Corridors among A–G whose final GIS status is YELLOW / DANGER / AT RISK)
            val_dangerous_roads = int(corr_df["status"].apply(
                lambda s: "DANGER" in str(s).upper() or "AT RISK" in str(s).upper() or "HIGH RISK" in str(s).upper() or "🟠" in str(s) or "🟡" in str(s)
            ).sum())

            # 4. Dynamic Metric: Road Blockages (Corridors among A–G whose final GIS status is RED / ROAD BLOCKAGE / BLOCKED)
            val_road_blockages = int(corr_df["status"].apply(
                lambda s: "BLOCKAGE" in str(s).upper() or "BLOCKED" in str(s).upper() or "CLOSED" in str(s).upper() or "🔴" in str(s)
            ).sum())

            # 5. Dynamic Metric: Weather Alerts
            val_weather_alerts = 0
            if live_w.get("rainfall", 0) > 0.0:
                val_weather_alerts += 1
            if live_w.get("wind", 0) > 25.0:
                val_weather_alerts += 1
            if w_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99]:
                val_weather_alerts += 1
            if active_mode == "Live GIS" and st.session_state.get("disaster_active", False):
                val_weather_alerts += 1
            if val_weather_alerts == 0 and live_w.get("humidity", 0) > 90:
                val_weather_alerts = 1

            # 6. Dynamic Road Blockage Alert Card
            if active_mode == "Live GIS":
                if st.session_state.get("disaster_active", False):
                    blockage_title = "NH-37 | Critical Landslide Detected"
                    blockage_desc = "Heavy rainfall triggered catastrophic slope failure on Silchar → Imphal. Corridor inaccessible. AI dynamic rerouting active."
                    blockage_tag = "DISASTER REROUTE ACTIVE"
                elif val_road_blockages > 0:
                    blocked_rows = corr_df[corr_df["status"].str.contains("BLOCKAGE|BLOCKED|CLOSED", case=False, na=False)]
                    if not blocked_rows.empty:
                        b_row = blocked_rows.iloc[0]
                        c_name = str(b_row.get("corridor", "Corridor"))
                        c_adv = str(b_row.get("advisory", "Road blockage indicated by live telemetry."))
                        blockage_title = f"{c_name} | Road Blockage Active"
                        blockage_desc = c_adv
                        blockage_tag = "LIVE CLOSURE ACTIVE"
                    else:
                        blockage_title = "Active Disruption Monitored"
                        blockage_desc = "Live telemetry indicates disruption on high-risk corridor segments."
                        blockage_tag = "LIVE ADVISORY ACTIVE"
                else:
                    blockage_title = "All Primary Corridors Clear"
                    blockage_desc = "No active road blockages reported across the NER logistics network. Standard transit corridors open."
                    blockage_tag = "NETWORK OPERATIONAL"
            else:
                # Real GPS Mode ground-truth alert
                if val_road_blockages > 0:
                    blockage_title = "Active Disruption Monitored"
                    blockage_desc = "Real-time atmospheric telemetry indicates disruption conditions on high-risk corridor segments."
                    blockage_tag = "LIVE ADVISORY ACTIVE"
                else:
                    blockage_title = "No Active Blockages Reported"
                    blockage_desc = "Live telemetry shows normal transit conditions across regional corridors. Weather conditions monitored via Open-Meteo."
                    blockage_tag = "LIVE NETWORK OPERATIONAL"

            # Weather Card (Layout, styling, and typography strictly preserved)
            st.markdown(h(f"""
            <div class="telemetry-weather-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase; font-weight:700;">REGIONAL WEATHER</div>
                        <div style="font-size:1.2rem; font-weight:800; color:#ffffff; font-family:'Outfit',sans-serif;">Guwahati Region</div>
                    </div>
                    <span style="font-size:2rem;">{w_icon}</span>
                </div>
                <div style="margin-top:8px; display:flex; align-items:baseline; gap:8px;">
                    <span style="font-size:1.8rem; font-weight:900; color:#38bdf8; font-family:'Outfit',sans-serif;">{w_temp_str}</span>
                    <span style="font-size:0.85rem; color:#cbd5e1;">{w_cond_str}</span>
                </div>
            </div>
            """), unsafe_allow_html=True)

            # Live KPI Metric Chips (Layout, styling, and typography strictly preserved)
            st.markdown(h(f"""
            <div class="telemetry-kpi-container">
                <div class="telemetry-kpi-chip">
                    <span class="kpi-dot green"></span>
                    <span class="kpi-label">Safe Roads</span>
                    <span class="kpi-val">{val_safe_roads}</span>
                </div>
                <div class="telemetry-kpi-chip">
                    <span class="kpi-dot yellow"></span>
                    <span class="kpi-label">Dangerous Roads</span>
                    <span class="kpi-val">{val_dangerous_roads}</span>
                </div>
                <div class="telemetry-kpi-chip">
                    <span class="kpi-dot red"></span>
                    <span class="kpi-label">Road Blockages</span>
                    <span class="kpi-val">{val_road_blockages}</span>
                </div>
                <div class="telemetry-kpi-chip">
                    <span class="kpi-dot pink"></span>
                    <span class="kpi-label">Weather Alerts</span>
                    <span class="kpi-val">{val_weather_alerts}</span>
                </div>
            </div>
            """), unsafe_allow_html=True)

            # Blockage Alert Card (Layout, styling, and typography strictly preserved)
            st.markdown(h(f"""
            <div class="telemetry-alert-card">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                    <span style="font-size:1.2rem;">⚠️</span>
                    <span style="font-size:0.82rem; font-weight:800; color:#f87171; text-transform:uppercase; letter-spacing:0.05em;">Road Blockage</span>
                </div>
                <div style="font-size:0.92rem; font-weight:700; color:#ffffff;">{blockage_title}</div>
                <p style="margin:4px 0 8px 0; font-size:0.78rem; color:#94a3b8; line-height:1.4;">
                    {blockage_desc}
                </p>
                <div style="display:inline-block; font-size:0.72rem; background:rgba(239, 68, 68, 0.2); color:#fca5a5; padding:2px 8px; border-radius:4px; font-weight:700;">
                    {blockage_tag}
                </div>
            </div>
            """), unsafe_allow_html=True)

        render_telemetry_live_panel(gis_vehicles, gis_incidents, gis_corridors, selected_mode)

    # ==========================================
    # BOTTOM SECTION: Role-Specific Command & Banner
    # ==========================================
    st.markdown("---")
    
    if user_role == "Field Officer":
        st.markdown(h("""
        <style>
        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] p {
            color: #FFFFFF !important;
        }
        </style>
        <h3 style="text-align:center; color:#FF0000;">Field Officer Command Console</h3>
        """), unsafe_allow_html=True)
        
        _, console_info_col, console_btn_col, _ = st.columns([0.7, 4.8, 2.3, 0.7], vertical_alignment="center")
        with console_info_col:
            st.info("Tactical command mode: Authorized for corridor status management, emergency rerouting, and cargo prioritization.")
        with console_btn_col:
            if st.button("⚡ Dispatch AI Re-route Directive", type="primary", use_container_width=True, key="btn_dispatch_ai_directive"):
                st.success("✅ Reroute order transmitted to Vehicle V03 and Assam Highway Command.")

        # Bottom Footer Banner matching mockup for Field Officer
        st.markdown(h("""
        <div class="overview-footer-banner">
            <span style="font-size:1.2rem; margin-right:8px;">🏔️</span>
            <span style="font-weight:700; color:#38bdf8; font-family:'Outfit',sans-serif;">Integrated Logistics Intelligence</span>
            <span style="color:#cbd5e1; margin-left:6px;">for a Stronger</span>
            <span style="color:#34d399; font-weight:800; margin-left:4px;">North East</span>
        </div>
        """), unsafe_allow_html=True)
    else:
        # =========================================================================
        # COMMERCIAL TRANSPORTER / PUBLIC USER LOGISTICS PORTAL
        # Clean, compact dark navy-blue dashboard panel matching SECOND reference image
        # =========================================================================
        st.markdown(h("""
        <style>
        /* Scoped Container Styling for Commercial Transporter Portal */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.public-portal-marker),
        .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:has(.public-portal-marker),
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .public-portal-marker) {
            background: rgba(10, 22, 44, 0.92) !important;
            background-color: rgba(10, 22, 44, 0.92) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(56, 189, 248, 0.28) !important;
            border-radius: 16px !important;
            padding: 22px 24px 18px 24px !important;
            box-shadow: 0 14px 34px rgba(0, 0, 0, 0.70), 0 0 16px rgba(56, 189, 248, 0.12) !important;
            margin-top: 12px !important;
            margin-bottom: 20px !important;
            max-width: 100% !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.public-portal-marker) > div,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.public-portal-marker) > div[data-testid="stVerticalBlock"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        .pub-title-wrap {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .pub-title-icon {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: rgba(56, 189, 248, 0.14);
            border: 1px solid rgba(56, 189, 248, 0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            box-shadow: 0 0 14px rgba(56, 189, 248, 0.25);
            flex-shrink: 0;
        }
        .pub-title-text {
            font-family: 'Outfit', sans-serif;
            font-size: 1.25rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.01em;
            line-height: 1.2;
        }
        .pub-sub-text {
            font-size: 0.80rem;
            color: #94a3b8;
            margin-top: 3px;
            line-height: 1.3;
        }
        .pub-metric-card {
            background: rgba(15, 23, 42, 0.80);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 14px;
            padding: 16px 18px;
            transition: transform 0.2s ease, border-color 0.2s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .pub-metric-card:hover {
            border-color: rgba(56, 189, 248, 0.4);
            transform: translateY(-2px);
        }
        .pub-metric-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 6px;
        }
        .pub-metric-label {
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #94a3b8;
        }
        .pub-metric-val {
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1;
            margin: 4px 0 8px 0;
        }
        .pub-metric-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            margin-bottom: 6px;
        }
        .pub-metric-badge.green {
            background: rgba(16, 185, 129, 0.16);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.32);
        }
        .pub-metric-badge.amber {
            background: rgba(245, 158, 11, 0.16);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.32);
        }
        .pub-metric-badge.red {
            background: rgba(239, 68, 68, 0.16);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.32);
        }
        .pub-metric-desc {
            font-size: 0.75rem;
            color: #cbd5e1;
            line-height: 1.35;
        }
        .pub-help-container {
            background: rgba(12, 25, 48, 0.96);
            border: 1px solid rgba(56, 189, 248, 0.40);
            border-radius: 14px;
            padding: 18px 20px;
            margin: 14px 0 18px 0;
            box-shadow: 0 10px 28px -4px rgba(0, 0, 0, 0.75);
        }

        /* Scoped Light Street/GIS Map Appearance for Help Interface */
        .pub-help-container div[data-testid="stDeckGlChart"],
        .pub-help-container div[data-testid="stDeckGlChart"] > div,
        .pub-help-container div[data-testid="stDeckGlChart"] canvas,
        .pub-help-container div[data-testid="stDeckGlChart"] .mapboxgl-map,
        .pub-help-container div[data-testid="stDeckGlChart"] .maplibregl-map {
            background-color: #f8fafc !important;
            background: #f8fafc !important;
        }
        .pub-help-container div[data-testid="stDeckGlChart"] {
            border: 2px solid rgba(56, 189, 248, 0.45) !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4) !important;
            margin-bottom: 10px !important;
        }
        .pub-help-container iframe {
            border: 2px solid rgba(56, 189, 248, 0.45) !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4) !important;
            margin-bottom: 8px !important;
            display: block !important;
            background-color: #f8fafc !important;
        }
        /* Small Clear Marker button styling */
        div.st-key-btn_clear_pub_map_marker button {
            padding: 2px 10px !important;
            font-size: 0.72rem !important;
            min-height: 28px !important;
            height: 28px !important;
            border-radius: 6px !important;
            background: rgba(239, 68, 68, 0.15) !important;
            border: 1px solid rgba(239, 68, 68, 0.45) !important;
            color: #f87171 !important;
            font-weight: 600 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }
        div.st-key-btn_clear_pub_map_marker button:hover {
            background: rgba(239, 68, 68, 0.35) !important;
            border-color: #ef4444 !important;
            color: #ffffff !important;
            box-shadow: 0 0 10px rgba(239, 68, 68, 0.4) !important;
        }
        </style>
        """), unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<div class="public-portal-marker"></div>', unsafe_allow_html=True)

            # Header Row with Title and Action Controls
            col_header, col_actions = st.columns([3.0, 0.75])
            with col_header:
                st.markdown(h("""
                <div class="pub-title-wrap">
                    <div class="pub-title-icon">👤</div>
                    <div>
                        <div class="pub-title-text">Public Transporter Logistics Portal</div>
                        <div class="pub-sub-text">General user view: Live accessibility and advisory information for commercial logistics and public motorists.</div>
                    </div>
                </div>
                """), unsafe_allow_html=True)

            with col_actions:
                help_is_open = st.session_state.get("show_public_help_modal", False)
                if help_is_open:
                    st.markdown("""
                    <style>
                    div.st-key-btn_toggle_pub_help button {
                        background-color: #FF4B4B !important;
                        background: #FF4B4B !important;
                        border: 1px solid #FF4B4B !important;
                        box-shadow: 0 2px 10px rgba(255, 75, 75, 0.45) !important;
                    }
                    div.st-key-btn_toggle_pub_help button,
                    div.st-key-btn_toggle_pub_help button *,
                    div.st-key-btn_toggle_pub_help button p,
                    div.st-key-btn_toggle_pub_help button span,
                    div.st-key-btn_toggle_pub_help button div {
                        color: #FFFFFF !important;
                        -webkit-text-fill-color: #FFFFFF !important;
                        font-weight: 700 !important;
                    }
                    div.st-key-btn_toggle_pub_help button:hover {
                        background-color: #e03e3e !important;
                        background: #e03e3e !important;
                        border-color: #e03e3e !important;
                        box-shadow: 0 4px 14px rgba(255, 75, 75, 0.65) !important;
                    }
                    div.st-key-btn_toggle_pub_help button:hover *,
                    div.st-key-btn_toggle_pub_help button:hover p,
                    div.st-key-btn_toggle_pub_help button:hover span {
                        color: #FFFFFF !important;
                        -webkit-text-fill-color: #FFFFFF !important;
                    }
                    div.st-key-btn_toggle_pub_help button:active {
                        background-color: #c93030 !important;
                        background: #c93030 !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                help_btn_label = "✕ Close Help" if help_is_open else "🆘 Need Help?"
                if st.button(help_btn_label, key="btn_toggle_pub_help", type="primary" if not help_is_open else "secondary", use_container_width=True):
                    st.session_state["show_public_help_modal"] = not help_is_open
                    st.rerun()

            if "real_gps_coord" in st.session_state and st.session_state["real_gps_coord"].get("lat") is not None:
                c_info = st.session_state["real_gps_coord"]
                st.markdown(f"""
                <div style="font-size:0.75rem; color:#34d399; font-weight:600; margin-top:-6px; margin-bottom:8px; text-align:right;">
                    🟢 Live Device GPS Active: {c_info['lat']:.4f}°N, {c_info['lon']:.4f}°E (±{c_info.get('accuracy', 10):.1f}m)
                </div>
                """, unsafe_allow_html=True)

            # Help Request Submission Confirmation
            if st.session_state.get("pub_help_submitted_msg"):
                st.success(st.session_state["pub_help_submitted_msg"])

            # --------------------------------------------------------
            # --------------------------------------------------------
            # COMPACT LOCATION & HELP REQUEST WINDOW
            # --------------------------------------------------------
            if st.session_state.get("show_public_help_modal", False):
                # Process any pending clear or coordinates update BEFORE widgets are instantiated
                if st.session_state.get("pub_clear_marker_requested"):
                    st.session_state["pub_marker_visible"] = False
                    st.session_state["pub_req_lat"] = None
                    st.session_state["pub_req_lon"] = None
                    st.session_state["pub_manual_lat"] = 0.0
                    st.session_state["pub_manual_lon"] = 0.0
                    st.session_state["pub_last_applied_click"] = None
                    st.session_state["pub_pending_coords"] = None
                    if "pub_help_folium_map" in st.session_state:
                        st.session_state["pub_help_folium_map"] = None
                    st.session_state["pub_clear_marker_requested"] = False
                elif st.session_state.get("pub_pending_coords"):
                    p_lat, p_lon = st.session_state["pub_pending_coords"]
                    st.session_state["pub_req_lat"] = p_lat
                    st.session_state["pub_req_lon"] = p_lon
                    st.session_state["pub_manual_lat"] = p_lat
                    st.session_state["pub_manual_lon"] = p_lon
                    st.session_state["pub_marker_visible"] = True
                    st.session_state["pub_pending_coords"] = None

                # Ensure coordinate session variables are initialized
                if "pub_req_lat" not in st.session_state:
                    st.session_state["pub_req_lat"] = 26.1445
                if "pub_req_lon" not in st.session_state:
                    st.session_state["pub_req_lon"] = 91.7362
                if "pub_manual_lat" not in st.session_state:
                    st.session_state["pub_manual_lat"] = float(st.session_state["pub_req_lat"] if st.session_state["pub_req_lat"] is not None else 0.0)
                if "pub_manual_lon" not in st.session_state:
                    st.session_state["pub_manual_lon"] = float(st.session_state["pub_req_lon"] if st.session_state["pub_req_lon"] is not None else 0.0)
                if "pub_marker_visible" not in st.session_state:
                    st.session_state["pub_marker_visible"] = True

                # Synchronize any previous map click event before rendering input fields
                prev_map_state = st.session_state.get("pub_help_folium_map")
                if prev_map_state and isinstance(prev_map_state, dict):
                    prev_click = prev_map_state.get("last_clicked")
                    if prev_click and isinstance(prev_click, dict) and prev_click.get("lat") is not None:
                        clk_lat = round(float(prev_click["lat"]), 6)
                        clk_lon = round(float(prev_click["lng"]), 6)
                        if st.session_state.get("pub_last_applied_click") != (clk_lat, clk_lon):
                            st.session_state["pub_last_applied_click"] = (clk_lat, clk_lon)
                            st.session_state["pub_req_lat"] = clk_lat
                            st.session_state["pub_req_lon"] = clk_lon
                            st.session_state["pub_manual_lat"] = clk_lat
                            st.session_state["pub_manual_lon"] = clk_lon
                            st.session_state["pub_marker_visible"] = True
                            st.session_state["pub_gps_msg"] = f"📍 Selected Map Location: {clk_lat:.4f}°N, {clk_lon:.4f}°E"

                st.markdown(h("""
                <div class="pub-help-container">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span style="font-size:1.3rem;">📍</span>
                            <div>
                                <div style="font-family:'Outfit',sans-serif; font-weight:800; font-size:1.05rem; color:#ffffff;">Live Location & Help Request</div>
                                <div style="font-size:0.75rem; color:#94a3b8;">Acquire device GPS telemetry or click map to select location for Field Ops dispatch</div>
                            </div>
                        </div>
                        <span style="display:inline-block; font-size:0.72rem; background:rgba(56, 189, 248, 0.15); color:#38bdf8; padding:3px 10px; border-radius:6px; font-weight:700; border:1px solid rgba(56, 189, 248, 0.35);">
                            TRANSPORTER DISPATCH
                        </span>
                    </div>
                </div>
                """), unsafe_allow_html=True)

                # Real Geolocation Control (Requests actual browser geolocation permission)
                hlp_col1, hlp_col2 = st.columns([1.2, 2.5])
                with hlp_col1:
                    st.markdown('<div style="font-size:0.80rem; font-weight:700; color:#38bdf8; margin-bottom:4px;">Use Live Location</div>', unsafe_allow_html=True)
                    gps_res = streamlit_geolocation()
                    if gps_res and isinstance(gps_res, dict) and gps_res.get("latitude") is not None:
                        fetched_lat = round(float(gps_res["latitude"]), 6)
                        fetched_lon = round(float(gps_res["longitude"]), 6)
                        fetched_acc = gps_res.get("accuracy", 10.0)
                        st.session_state["real_gps_coord"] = {
                            "lat": fetched_lat,
                            "lon": fetched_lon,
                            "accuracy": fetched_acc
                        }
                        if st.session_state.get("gps_already_applied") != (fetched_lat, fetched_lon):
                            st.session_state["gps_already_applied"] = (fetched_lat, fetched_lon)
                            st.session_state["pub_req_lat"] = fetched_lat
                            st.session_state["pub_req_lon"] = fetched_lon
                            st.session_state["pub_pending_coords"] = (fetched_lat, fetched_lon)
                            st.session_state["pub_marker_visible"] = True
                            st.session_state["pub_last_applied_click"] = (fetched_lat, fetched_lon)
                            if "pub_help_folium_map" in st.session_state:
                                st.session_state["pub_help_folium_map"] = None
                            st.session_state["pub_gps_msg"] = f"🟢 Live GPS Acquired: {fetched_lat:.4f}°N, {fetched_lon:.4f}°E (±{fetched_acc:.1f}m)"
                            st.rerun()
                    elif gps_res and isinstance(gps_res, dict) and gps_res.get("error"):
                        st.session_state["pub_gps_msg"] = f"⚠️ Location unavailable ({gps_res.get('error')}). Manual coordinates or map click active."

                with hlp_col2:
                    if st.session_state.get("pub_gps_msg"):
                        st.markdown(f'<div style="font-size:0.80rem; color:#34d399; font-weight:700; padding:8px 12px; background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.35); border-radius:8px; margin-top:14px;">{st.session_state["pub_gps_msg"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="font-size:0.78rem; color:#94a3b8; padding:8px 12px; background:rgba(255,255,255,0.05); border-radius:8px; margin-top:14px;">📍 Click "Use Live Location", click anywhere on the map, or enter coordinates manually.</div>', unsafe_allow_html=True)

                # Coordinate inputs (Manual editing supported)
                coord_c1, coord_c2 = st.columns(2)
                with coord_c1:
                    input_lat = st.number_input(
                        "Latitude (°N)",
                        value=float(st.session_state["pub_manual_lat"]),
                        format="%.6f",
                        step=0.0001,
                        key="pub_manual_lat"
                    )
                with coord_c2:
                    input_lon = st.number_input(
                        "Longitude (°E)",
                        value=float(st.session_state["pub_manual_lon"]),
                        format="%.6f",
                        step=0.0001,
                        key="pub_manual_lon"
                    )

                # Synchronize manual user typing
                if input_lat != 0.0 and input_lon != 0.0:
                    if (st.session_state.get("pub_req_lat") != input_lat or 
                        st.session_state.get("pub_req_lon") != input_lon or 
                        not st.session_state.get("pub_marker_visible", True)):
                        st.session_state["pub_req_lat"] = input_lat
                        st.session_state["pub_req_lon"] = input_lon
                        st.session_state["pub_marker_visible"] = True
                        st.session_state["pub_last_applied_click"] = (input_lat, input_lon)

                # Map Header with Small Clear / Erase Control
                map_bar_col1, map_bar_col2 = st.columns([3.2, 1.0])
                with map_bar_col1:
                    st.markdown('<div style="font-size:0.76rem; color:#94a3b8; font-weight:600; padding-top:6px;">🗺️ Interactive Map (Click to place/move marker)</div>', unsafe_allow_html=True)
                with map_bar_col2:
                    if st.button("✕ Clear Marker", key="btn_clear_pub_map_marker", help="Remove red pin marker and reset selected coordinates"):
                        st.session_state["pub_clear_marker_requested"] = True
                        st.session_state["pub_marker_visible"] = False
                        st.session_state["pub_req_lat"] = None
                        st.session_state["pub_req_lon"] = None
                        st.session_state["pub_last_applied_click"] = None
                        st.session_state["pub_pending_coords"] = None
                        if "real_gps_coord" in st.session_state and st.session_state["real_gps_coord"].get("lat") is not None:
                            st.session_state["gps_already_applied"] = (st.session_state["real_gps_coord"]["lat"], st.session_state["real_gps_coord"]["lon"])
                        if "pub_help_folium_map" in st.session_state:
                            st.session_state["pub_help_folium_map"] = None
                        st.session_state["pub_gps_msg"] = "ℹ️ Marker cleared. Click the map or enter coordinates to select a location."
                        st.rerun()

                # Determine active marker and map center
                has_active_marker = (
                    st.session_state.get("pub_marker_visible", True)
                    and st.session_state.get("pub_req_lat") is not None
                    and st.session_state.get("pub_req_lat") != 0.0
                    and st.session_state.get("pub_req_lon") is not None
                    and st.session_state.get("pub_req_lon") != 0.0
                )

                if has_active_marker:
                    map_center_lat = float(st.session_state["pub_req_lat"])
                    map_center_lon = float(st.session_state["pub_req_lon"])
                    map_zoom = 12
                else:
                    map_center_lat = 26.1445
                    map_center_lon = 91.7362
                    map_zoom = 9

                # Interactive Folium Map with OpenStreetMap tiles (light GIS / street style)
                hlp_folium_map = folium.Map(
                    location=[map_center_lat, map_center_lon],
                    zoom_start=map_zoom,
                    tiles="OpenStreetMap",
                    control_scale=False
                )
                Fullscreen(position="topright").add_to(hlp_folium_map)

                # Ensure only ONE single active red location marker
                if has_active_marker:
                    folium.Marker(
                        location=[map_center_lat, map_center_lon],
                        tooltip=f"Selected Location: {map_center_lat:.4f}°N, {map_center_lon:.4f}°E",
                        icon=folium.Icon(color="red", icon="info-sign")
                    ).add_to(hlp_folium_map)
                    folium.Circle(
                        location=[map_center_lat, map_center_lon],
                        radius=250,
                        color="#ef4444",
                        weight=1.5,
                        fill=True,
                        fill_color="#ef4444",
                        fill_opacity=0.18
                    ).add_to(hlp_folium_map)

                # Render Interactive Folium Map and capture click events
                map_out = st_folium(
                    hlp_folium_map,
                    height=210,
                    use_container_width=True,
                    returned_objects=["last_clicked"],
                    key="pub_help_folium_map"
                )

                # Capture map click immediately if received on this run
                if map_out and isinstance(map_out, dict):
                    click_res = map_out.get("last_clicked")
                    if click_res and isinstance(click_res, dict) and click_res.get("lat") is not None:
                        clk_lat = round(float(click_res["lat"]), 6)
                        clk_lon = round(float(click_res["lng"]), 6)
                        if st.session_state.get("pub_last_applied_click") != (clk_lat, clk_lon):
                            st.session_state["pub_last_applied_click"] = (clk_lat, clk_lon)
                            st.session_state["pub_req_lat"] = clk_lat
                            st.session_state["pub_req_lon"] = clk_lon
                            st.session_state["pub_pending_coords"] = (clk_lat, clk_lon)
                            st.session_state["pub_marker_visible"] = True
                            st.session_state["pub_gps_msg"] = f"📍 Selected Map Location: {clk_lat:.4f}°N, {clk_lon:.4f}°E"
                            st.rerun()

                help_desc = st.text_area(
                    "Assistance Description",
                    placeholder="Describe vehicle details (e.g. Truck number, cargo type), situation, specific landmark or assistance required...",
                    height=85,
                    max_chars=300,
                    key="pub_help_details_input"
                )

                act_btn1, act_btn2 = st.columns([1.5, 1])
                with act_btn1:
                    if st.button("🚀 Submit Help Request", type="primary", use_container_width=True, key="btn_submit_pub_help"):
                        if not help_desc.strip():
                            st.error("Please provide a description of the required assistance.")
                        elif not st.session_state.get("pub_marker_visible", True) and (input_lat == 0.0 or input_lon == 0.0):
                            st.error("Please select a location on the map or click 'Use Live Location' before submitting.")
                        else:
                            created_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            unique_suffix = int(time.time() * 1000) % 1000000
                            report_id = f"NER-PUB-HELP-{unique_suffix:06d}"

                            user_disp_name = st.session_state.get("user_name", "Public Transporter")
                            user_id_val = st.session_state.get("officer_id", "PUB-TRP-01")
                            user_role_val = st.session_state.get("user_role", "Commercial Transporter")
                            user_org_val = st.session_state.get("organization", "NorthEast Express Logistics")

                            sub_lat = float(input_lat) if (input_lat and input_lat != 0.0) else float(st.session_state.get("pub_req_lat") or 26.1445)
                            sub_lon = float(input_lon) if (input_lon and input_lon != 0.0) else float(st.session_state.get("pub_req_lon") or 91.7362)

                            report_data = {
                                "help_request_id": report_id,
                                "timestamp": created_ts,
                                "latitude": round(sub_lat, 6),
                                "longitude": round(sub_lon, 6),
                                "description": help_desc.strip(),
                                "requester": {
                                    "name": user_disp_name,
                                    "user_id": user_id_val,
                                    "role": user_role_val,
                                    "organization": user_org_val
                                },
                                "status": "New",
                                "type": "Public Help Request"
                            }

                            _save_public_help_request(report_data)
                            if "public_help_requests" not in st.session_state:
                                st.session_state.public_help_requests = []
                            st.session_state.public_help_requests.append(report_data)

                            st.session_state["pub_help_submitted_msg"] = f"✅ Help Request {report_id} submitted with status 'New'. Transmitted to Regional Field Ops."
                            st.session_state["show_public_help_modal"] = False
                            st.rerun()

                with act_btn2:
                    if st.button("✕ Cancel / Close", use_container_width=True, key="btn_cancel_pub_help"):
                        st.session_state["show_public_help_modal"] = False
                        st.rerun()

            # --------------------------------------------------------
            # THREE CORRIDOR STATUS CARDS (Matching Second Reference Image)
            # --------------------------------------------------------
            if gis_corridors is not None and "status" in gis_corridors.columns:
                pub_safe_count = int(gis_corridors["status"].apply(
                    lambda s: str(s).strip().upper() == "SAFE" or "ACCESSIBLE" in str(s).upper() or "🟢" in str(s)
                ).sum())
                pub_at_risk_count = int(gis_corridors["status"].apply(
                    lambda s: "DANGER" in str(s).upper() or "AT RISK" in str(s).upper() or "HIGH RISK" in str(s).upper() or "🟠" in str(s) or "🟡" in str(s)
                ).sum())
            else:
                status_col = "Status" if "Status" in corridor_data.columns else "status"
                pub_safe_count = int(corridor_data[status_col].str.contains("SAFE|ACCESSIBLE|🟢", case=False, na=False).sum())
                pub_at_risk_count = int(corridor_data[status_col].str.contains("DANGER|AT RISK|HIGH RISK|🟠|🟡", case=False, na=False).sum())

            gc1, gc2, gc3 = st.columns(3)
            with gc1:
                st.markdown(h(f"""
                <div class="pub-metric-card">
                    <div class="pub-metric-header">
                        <span class="pub-metric-label">🛣️ SAFE CORRIDORS</span>
                        <span style="width:8px; height:8px; border-radius:50%; background:#10b981; box-shadow:0 0 8px #10b981; display:inline-block;"></span>
                    </div>
                    <div class="pub-metric-val">{pub_safe_count}</div>
                    <div>
                        <div class="pub-metric-badge green">
                            <span>↑</span> +2 Cleared Today
                        </div>
                    </div>
                    <div class="pub-metric-desc">
                        Normal network flow maintained across primary freight arteries. Optimal transit windows active.
                    </div>
                </div>
                """), unsafe_allow_html=True)

            with gc2:
                st.markdown(h(f"""
                <div class="pub-metric-card">
                    <div class="pub-metric-header">
                        <span class="pub-metric-label">⚠️ AT-RISK CORRIDORS</span>
                        <span style="width:8px; height:8px; border-radius:50%; background:#f59e0b; box-shadow:0 0 8px #f59e0b; display:inline-block;"></span>
                    </div>
                    <div class="pub-metric-val">{pub_at_risk_count}</div>
                    <div>
                        <div class="pub-metric-badge amber">
                            <span>⚠️</span> Rainfall Advisory
                        </div>
                    </div>
                    <div class="pub-metric-desc">
                        Heavy precipitation monitored on hill corridors (Silchar → Imphal & Dimapur). Slope stability sensors active.
                    </div>
                </div>
                """), unsafe_allow_html=True)

            with gc3:
                status_col = "Status" if "Status" in corridor_data.columns else "status"
                corr_col = "Corridor" if "Corridor" in corridor_data.columns else "corridor"
                adv_col = "Advisory" if "Advisory" in corridor_data.columns else "advisory"
                pub_blocked_count = int(corridor_data[status_col].str.contains("BLOCKAGE|BLOCKED|CLOSED|🔴", case=False, na=False).sum())
                if pub_blocked_count > 0:
                    b_rows = corridor_data[corridor_data[status_col].str.contains("BLOCKAGE|BLOCKED|CLOSED|🔴", case=False, na=False)]
                    b_name = b_rows.iloc[0].get(corr_col, "Corridor") if not b_rows.empty else "Corridor"
                    b_adv = b_rows.iloc[0].get(adv_col, "Diversion active.") if not b_rows.empty else "Diversion active."
                    st.markdown(h(f"""
                    <div class="pub-metric-card">
                        <div class="pub-metric-header">
                            <span class="pub-metric-label">🚧 BLOCKED CORRIDORS</span>
                            <span style="width:8px; height:8px; border-radius:50%; background:#ef4444; box-shadow:0 0 8px #ef4444; display:inline-block;"></span>
                        </div>
                        <div class="pub-metric-val">{pub_blocked_count}</div>
                        <div>
                            <div class="pub-metric-badge red">
                                <span>⛔</span> {b_name} Diversion Active
                            </div>
                        </div>
                        <div class="pub-metric-desc">
                            {b_adv}
                        </div>
                    </div>
                    """), unsafe_allow_html=True)
                else:
                    st.markdown(h("""
                    <div class="pub-metric-card">
                        <div class="pub-metric-header">
                            <span class="pub-metric-label">🚧 BLOCKED CORRIDORS</span>
                            <span style="width:8px; height:8px; border-radius:50%; background:#10b981; box-shadow:0 0 8px #10b981; display:inline-block;"></span>
                        </div>
                        <div class="pub-metric-val">0</div>
                        <div>
                            <div class="pub-metric-badge green">
                                <span>🟢</span> All Corridors Clear
                            </div>
                        </div>
                        <div class="pub-metric-desc">
                            No active road closures reported across regional freight arteries. Optimal transit active.
                        </div>
                    </div>
                    """), unsafe_allow_html=True)

            # --------------------------------------------------------
            # INTEGRATED LOGISTICS INTELLIGENCE BANNER (Inside Panel)
            # --------------------------------------------------------
            st.markdown(h("""
            <div class="overview-footer-banner" style="margin-top: 18px; margin-bottom: 2px; background: rgba(15, 23, 42, 0.72); border: 1px solid rgba(56, 189, 248, 0.2);">
                <span style="font-size:1.2rem; margin-right:8px;">🏔️</span>
                <span style="font-weight:700; color:#38bdf8; font-family:'Outfit',sans-serif;">Integrated Logistics Intelligence</span>
                <span style="color:#cbd5e1; margin-left:6px;">for a Stronger</span>
                <span style="color:#34d399; font-weight:800; margin-left:4px;">North East</span>
            </div>
            """), unsafe_allow_html=True)


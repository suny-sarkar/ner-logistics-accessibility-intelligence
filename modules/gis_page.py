import streamlit as st
import pandas as pd
import pydeck as pdk
import folium
from streamlit_folium import st_folium
import networkx as nx
import requests
from streamlit_geolocation import streamlit_geolocation
from modules.road_status_provider import get_authoritative_corridor_status, get_static_fallback_corridors


def render_gis_page():
    # PART 2 — NER GIS ACCESSIBILITY & VEHICLE TRACKING
    # ============================================================
    
    st.markdown('<div id="gis-map-section"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    /* ============================================================
       VEHICLE GPS CONTROL PANEL — SOLID DARK NAVY (#062B55)
       Scoped strictly via .vehicle-gps-panel-marker.
       Zero global impact.
       ============================================================ */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker),
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker),
    .block-container > div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stElementContainer"] .vehicle-gps-panel-marker),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .vehicle-gps-panel-marker) {
        background: #062B55 !important;
        background-color: #062B55 !important;
        opacity: 1 !important;
        border: 1px solid rgba(32, 196, 255, 0.45) !important;
        border-radius: 13px !important;
        padding: 22px 28px !important;
        margin: 0 auto 20px auto !important;
        max-width: 1060px !important;
        width: 100% !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.60), inset 0 0 16px rgba(32, 196, 255, 0.08) !important;
        transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) > div,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) > div[data-testid="stVerticalBlock"] {
        background: #062B55 !important;
        background-color: #062B55 !important;
        opacity: 1 !important;
        border: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker):hover,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .vehicle-gps-panel-marker):hover {
        border-color: rgba(32, 196, 255, 0.70) !important;
        box-shadow: 0 12px 34px rgba(0, 0, 0, 0.70), inset 0 0 20px rgba(32, 196, 255, 0.12), 0 0 14px rgba(32, 196, 255, 0.25) !important;
    }

    /* Sub-blocks & element containers inside the panel stay transparent */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) div[data-testid="stVerticalBlock"]:not(:has(> div[data-testid="stElementContainer"] .vehicle-gps-panel-marker)),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .vehicle-gps-panel-marker) div[data-testid="stVerticalBlock"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) div[data-testid="stElementContainer"],
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .vehicle-gps-panel-marker) div[data-testid="stElementContainer"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Selectbox inside the panel */
    div:has(.vehicle-gps-panel-marker) [data-testid="stSelectbox"] label,
    div:has(.vehicle-gps-panel-marker) [data-testid="stSelectbox"] label *,
    div:has(.vehicle-gps-panel-marker) [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] *,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) [data-testid="stSelectbox"] label,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) [data-testid="stSelectbox"] label p,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) [data-testid="stSelectbox"] label span,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) [data-testid="stSelectbox"] [data-testid="stWidgetLabel"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] p,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.90rem !important;
        margin-bottom: 6px !important;
    }

    /* Radio buttons (GPS Mode, Simulation, Real GPS) inside the Vehicle GPS Control panel — Pure White (#FFFFFF) */
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] *,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] label,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] label *,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] label p,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] label span,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] [data-testid="stWidgetLabel"],
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] [data-testid="stWidgetLabel"] *,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] [data-testid="stWidgetLabel"] p,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] [data-testid="stMarkdownContainer"],
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] [data-testid="stMarkdownContainer"] *,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] div[role="radiogroup"] *,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] div[role="radiogroup"] label,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] div[role="radiogroup"] label *,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] div[role="radiogroup"] p,
    div:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] div[role="radiogroup"] span,
    div:has(.vehicle-gps-panel-marker) [data-baseweb="radio"],
    div:has(.vehicle-gps-panel-marker) [data-baseweb="radio"] *,
    div:has(.vehicle-gps-panel-marker) [data-baseweb="radio"] label,
    div:has(.vehicle-gps-panel-marker) [data-baseweb="radio"] p,
    div:has(.vehicle-gps-panel-marker) [data-baseweb="radio"] span,
    div:has(.vehicle-gps-panel-marker) [data-baseweb="radio"] div,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] *,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] p,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) [data-testid="stRadio"] span,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .vehicle-gps-panel-marker) [data-testid="stRadio"] *,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .vehicle-gps-panel-marker) [data-testid="stRadio"] p,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .vehicle-gps-panel-marker) [data-testid="stRadio"] span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        opacity: 1 !important;
    }

    /* Metrics if Real GPS is active */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) [data-testid="stMetricValue"] {
        color: #38BDF8 !important;
        font-family: 'Outfit', sans-serif !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.vehicle-gps-panel-marker) [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
        font-family: 'Outfit', sans-serif !important;
    }

    /* ============================================================
       GIS FLEET MAP CONTAINER — MATCHES EXACT PANEL WIDTH (1060px)
       ============================================================ */
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .gis-fleet-map-marker),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .gis-fleet-map-marker),
    div:has(> div[data-testid="stElementContainer"] .gis-fleet-map-marker) {
        max-width: 1060px !important;
        width: 100% !important;
        margin: 0 auto 24px auto !important;
    }

    div:has(.gis-fleet-map-marker) .overview-map-hud-header {
        background: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(32, 196, 255, 0.45) !important;
        border-bottom: none !important;
        border-radius: 13px 13px 0 0 !important;
        padding: 8px 14px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        margin-bottom: 0 !important;
        max-width: 1060px !important;
        width: 100% !important;
        box-sizing: border-box !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    div:has(.gis-fleet-map-marker) div[data-testid="stDeckGlChart"],
    div:has(.gis-fleet-map-marker) div[data-testid="stDeckGlChart"] > div,
    div:has(.gis-fleet-map-marker) div[data-testid="stDeckGlChart"] canvas,
    div:has(.gis-fleet-map-marker) div[data-testid="stDeckGlChart"] .mapboxgl-map,
    div:has(.gis-fleet-map-marker) div[data-testid="stDeckGlChart"] .maplibregl-map {
        background-color: #0b0f19 !important;
        background: #0b0f19 !important;
    }

    div:has(.gis-fleet-map-marker) div[data-testid="stDeckGlChart"] {
        border: 1px solid rgba(32, 196, 255, 0.45) !important;
        border-top: none !important;
        border-radius: 0 0 13px 13px !important;
        overflow: hidden !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.60), inset 0 0 16px rgba(32, 196, 255, 0.08) !important;
        margin: 0 auto !important;
        max-width: 1060px !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }

    div:has(.gis-fleet-map-marker) div[data-testid="stDeckGlChart"] > div {
        border-radius: 0 0 13px 13px !important;
        overflow: hidden !important;
        max-width: 1060px !important;
        width: 100% !important;
    }

    /* ============================================================
       TABLE CONTAINERS — MATCHES 1060px PANEL WIDTH
       ============================================================ */
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .live-movement-container-marker),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .live-movement-container-marker),
    div:has(> div[data-testid="stElementContainer"] .live-movement-container-marker),
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .corridor-accessibility-container-marker),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .corridor-accessibility-container-marker),
    div:has(> div[data-testid="stElementContainer"] .corridor-accessibility-container-marker) {
        max-width: 1060px !important;
        width: 100% !important;
        margin: 0 auto 20px auto !important;
    }

    div:has(.live-movement-container-marker) [data-testid="stDataFrame"],
    div:has(.live-movement-container-marker) [data-testid="stDataFrame"] > div,
    div:has(.live-movement-container-marker) [data-testid="stTable"],
    div:has(.corridor-accessibility-container-marker) [data-testid="stDataFrame"],
    div:has(.corridor-accessibility-container-marker) [data-testid="stDataFrame"] > div,
    div:has(.corridor-accessibility-container-marker) [data-testid="stTable"] {
        max-width: 1060px !important;
        width: 100% !important;
        margin: 0 auto !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin: 1.25rem auto 1.75rem auto; max-width: 850px; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; box-sizing: border-box; padding: 0 1rem;">
        <h2 style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.75rem; font-weight: 700; color: #FFFFFF; margin: 0 0 0.45rem 0; text-align: center; line-height: 1.25; letter-spacing: -0.01em;">NER Logistics Accessibility Map</h2>
        <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 0.95rem; font-weight: 400; color: rgba(255, 255, 255, 0.75); text-align: center; line-height: 1.55; max-width: 680px; margin: 0 auto;">Prototype GIS view showing simulated vehicle movement, road accessibility and disruption points.</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ------------------------------------------------------------
    # Simulated NER logistics network
    # ------------------------------------------------------------
    
    locations = pd.DataFrame([
        {
            "name": "Guwahati Hub",
            "lat": 26.1445,
            "lon": 91.7362,
            "type": "Warehouse"
        },
        {
            "name": "Imphal",
            "lat": 24.8170,
            "lon": 93.9368,
            "type": "Destination"
        },
        {
            "name": "Shillong",
            "lat": 25.5788,
            "lon": 91.8933,
            "type": "Destination"
        },
        {
            "name": "Aizawl",
            "lat": 23.7271,
            "lon": 92.7176,
            "type": "Destination"
        },
        {
            "name": "Agartala",
            "lat": 23.8315,
            "lon": 91.2868,
            "type": "Destination"
        }
    ])
    
    # ------------------------------------------------------------
    # Simulated vehicles
    # ------------------------------------------------------------
    
    vehicles = pd.DataFrame([
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
    
    # ------------------------------------------------------------
    # Vehicle GPS Control
    # ------------------------------------------------------------
    
    with st.container(border=True):
        st.markdown('<div class="vehicle-gps-panel-marker"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 12px; letter-spacing: -0.01em;">
            Vehicle GPS Control
        </div>
        """, unsafe_allow_html=True)
        
        selected_vehicle = st.selectbox(
            "Select Vehicle",
            vehicles["vehicle"].tolist()
        )
        
        gps_mode = st.radio(
            "GPS Mode",
            ["Simulation", "Real GPS"],
            horizontal=True
        )
        
        # ------------------------------------------------------------
        # GPS variables — initialize BEFORE using them
        # ------------------------------------------------------------
        
        gps_available = False
        gps_lat = None
        gps_lon = None
        gps_accuracy = None
        
        # ------------------------------------------------------------
        # Real GPS Tracking
        # ------------------------------------------------------------
        
        if gps_mode == "Real GPS":
        
            st.markdown("#### 📍 Real GPS Tracking")
        
            location = streamlit_geolocation()
        
            if location and location.get("latitude") is not None:
        
                gps_available = True
        
                gps_lat = float(location["latitude"])
                gps_lon = float(location["longitude"])
                gps_accuracy = location.get("accuracy")
        
                st.success("🟢 Real GPS location acquired")
        
                col1, col2, col3 = st.columns(3)
        
                with col1:
                    st.metric(
                        "Latitude",
                        f"{gps_lat:.6f}"
                    )
        
                with col2:
                    st.metric(
                        "Longitude",
                        f"{gps_lon:.6f}"
                    )
        
                with col3:
                    st.metric(
                        "Accuracy",
                        f"{gps_accuracy:.1f} m"
                        if gps_accuracy is not None
                        else "N/A"
                    )
        
            else:
        
                st.info(
                    "📍 Click the location button and allow browser location access."
                )
        
        # ------------------------------------------------------------
        # Real GPS → Selected Vehicle
        # ------------------------------------------------------------
        
        if gps_mode == "Real GPS" and gps_available:
        
            vehicles.loc[
                vehicles["vehicle"] == selected_vehicle,
                "lat"
            ] = gps_lat
        
            vehicles.loc[
                vehicles["vehicle"] == selected_vehicle,
                "lon"
            ] = gps_lon
        
            vehicles.loc[
                vehicles["vehicle"] == selected_vehicle,
                "status"
            ] = "LIVE GPS"
        
            st.success(
                f"📍 {selected_vehicle} is now using live GPS coordinates."
            )
        
    # ------------------------------------------------------------
    # EXACT HOME-PAGE FUNCTIONAL GIS MAP REUSED
    # ------------------------------------------------------------

    # Geographic landmarks/nodes of the NER logistics network (from Home page)
    gis_locations = pd.DataFrame([
        {"name": "Guwahati Hub", "lat": 26.1445, "lon": 91.7362, "type": "Warehouse Hub", "status": "Active Hub", "advisory": "", "cargo": "", "vehicle": "", "incident": ""},
        {"name": "Imphal", "lat": 24.8170, "lon": 93.9368, "type": "Regional Destination", "status": "Active Hub", "advisory": "", "cargo": "", "vehicle": "", "incident": ""},
        {"name": "Shillong", "lat": 25.5788, "lon": 91.8933, "type": "Regional Destination", "status": "Active Hub", "advisory": "", "cargo": "", "vehicle": "", "incident": ""},
        {"name": "Aizawl", "lat": 23.7271, "lon": 92.7176, "type": "Regional Destination", "status": "Active Hub", "advisory": "", "cargo": "", "vehicle": "", "incident": ""},
        {"name": "Agartala", "lat": 23.8315, "lon": 91.2868, "type": "Regional Destination", "status": "Active Hub", "advisory": "", "cargo": "", "vehicle": "", "incident": ""},
        {"name": "Dimapur", "lat": 25.9000, "lon": 93.7200, "type": "Logistics Junction", "status": "Active Hub", "advisory": "", "cargo": "", "vehicle": "", "incident": ""},
        {"name": "Kohima", "lat": 25.6700, "lon": 94.1100, "type": "Regional Destination", "status": "Active Hub", "advisory": "", "cargo": "", "vehicle": "", "incident": ""},
        {"name": "Silchar", "lat": 24.8333, "lon": 92.7976, "type": "Transit Hub", "status": "Active Hub", "advisory": "", "cargo": "", "vehicle": "", "incident": ""},
        {"name": "Tezpur", "lat": 26.6300, "lon": 92.8000, "type": "Transit Node", "status": "Active Hub", "advisory": "", "cargo": "", "vehicle": "", "incident": ""},
        {"name": "Itanagar", "lat": 27.1000, "lon": 93.6200, "type": "Regional Destination", "status": "Active Hub", "advisory": "", "cargo": "", "vehicle": "", "incident": ""}
    ])

    # Authoritative GIS Road-Status Data Layer (Shared Live TomTom Traffic Data with Home GIS)
    try:
        gis_corridors, corridor_data, _corridor_meta = get_authoritative_corridor_status()
    except Exception:
        gis_corridors, corridor_data, _corridor_meta = get_static_fallback_corridors()

    # Ensure auxiliary fields exist for PyDeck tooltip compatibility
    for _col in ["cargo", "vehicle", "incident"]:
        if _col not in gis_corridors.columns:
            gis_corridors[_col] = ""


    # Disruption points (from Home page)
    gis_incidents = pd.DataFrame([
        {
            "name": "High Risk Corridor",
            "lat": 24.95,
            "lon": 92.70,
            "risk": "82%",
            "incident": "Heavy Rainfall / Landslide Risk",
            "status": "AT RISK",
            "advisory": "Precipitation Monitored",
            "cargo": "",
            "vehicle": ""
        }
    ])

    # Supply & Cargo markers (from Home page)
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

    # MAP LAYERS (Matching Home page exactly)
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
        data=vehicles,
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

    # Integrated Container: HUD Header + DeckGL Map (Exact width matched to Vehicle GPS Control)
    with st.container():
        st.markdown('<div class="gis-fleet-map-marker"></div>', unsafe_allow_html=True)
        st.markdown("""
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
        """, unsafe_allow_html=True)

        st.pydeck_chart(deck, use_container_width=True, height=480)
    
    # ------------------------------------------------------------
    # Vehicle status table
    # ------------------------------------------------------------
    
    with st.container():
        st.markdown('<div class="live-movement-container-marker"></div>', unsafe_allow_html=True)
        st.markdown("### Live Logistics Movement")
        st.dataframe(
            vehicles[
                [
                    "vehicle",
                    "cargo",
                    "destination",
                    "eta",
                    "status"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )
    
    # ------------------------------------------------------------
    # Accessibility status
    # ------------------------------------------------------------
    
    with st.container():
        st.markdown('<div class="corridor-accessibility-container-marker"></div>', unsafe_allow_html=True)
        st.markdown("### Corridor Accessibility")
        
        st.dataframe(
            corridor_data,
            use_container_width=True,
            hide_index=True
        )
    
    # ============================================================


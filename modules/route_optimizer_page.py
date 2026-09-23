import streamlit as st
import pandas as pd
import textwrap
import pydeck as pdk
import folium
from streamlit_folium import st_folium
import networkx as nx
import requests
from streamlit_geolocation import streamlit_geolocation
from modules.road_status_provider import get_authoritative_corridor_status, get_static_fallback_corridors


def h(html_str):
    return "".join(line.strip() for line in html_str.strip().splitlines() if line.strip())

def render_route_optimizer_page():
    # DISASTER SIMULATION + DYNAMIC ROUTE OPTIMIZATION
    # ---------------------------------------------------------
    
    st.markdown('<div id="route-opt-section"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    /* ============================================================
       AI ROUTE PAGE CONTAINMENT
       Root vertical block stays transparent so mountain background
       is visible outside and between panels.
       Zero page-level blue overlay.
       ============================================================ */
    .block-container > div[data-testid="stVerticalBlock"] {
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        border: none !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    /* ROUTE PANELS — SOLID DARK NAVY (#062B55) */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker),
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker),
    .block-container > div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stElementContainer"] .route-opt-panel-marker),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .route-opt-panel-marker),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-rec-panel-marker),
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-rec-panel-marker),
    .block-container > div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stElementContainer"] .route-rec-panel-marker),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .route-rec-panel-marker) {
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

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) > div,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) > div[data-testid="stVerticalBlock"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-rec-panel-marker) > div,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-rec-panel-marker) > div[data-testid="stVerticalBlock"] {
        background: #062B55 !important;
        background-color: #062B55 !important;
        opacity: 1 !important;
        border: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker):hover,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .route-opt-panel-marker):hover,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-rec-panel-marker):hover,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .route-rec-panel-marker):hover {
        border-color: rgba(32, 196, 255, 0.70) !important;
        box-shadow: 0 12px 34px rgba(0, 0, 0, 0.70), inset 0 0 20px rgba(32, 196, 255, 0.12), 0 0 14px rgba(32, 196, 255, 0.25) !important;
    }

    /* Sub-blocks & element containers inside the panels stay transparent */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) div[data-testid="stVerticalBlock"]:not(:has(> div[data-testid="stElementContainer"] .route-opt-panel-marker)),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .route-opt-panel-marker) div[data-testid="stVerticalBlock"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) div[data-testid="stElementContainer"],
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .route-opt-panel-marker) div[data-testid="stElementContainer"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-rec-panel-marker) div[data-testid="stVerticalBlock"]:not(:has(> div[data-testid="stElementContainer"] .route-rec-panel-marker)),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .route-rec-panel-marker) div[data-testid="stElementContainer"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-rec-panel-marker) div[data-testid="stElementContainer"],
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .route-rec-panel-marker) div[data-testid="stElementContainer"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Toggle Switch inside the panel — pure white (#FFFFFF) */
    [data-testid="stToggle"] {
        display: flex !important;
        align-items: center !important;
        margin-top: 10px !important;
    }

    [data-testid="stToggle"] label,
    [data-testid="stToggle"] label *,
    [data-testid="stToggle"] p,
    [data-testid="stToggle"] span,
    [data-testid="stToggle"] div,
    [data-testid="stToggle"] [data-testid="stWidgetLabel"],
    [data-testid="stToggle"] [data-testid="stWidgetLabel"] *,
    [data-testid="stToggle"] [data-testid="stMarkdownContainer"],
    [data-testid="stToggle"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stToggle"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stToggle"] [data-testid="stMarkdownContainer"] span,
    div:has(.sim-toggle-container) [data-testid="stToggle"] label,
    div:has(.sim-toggle-container) [data-testid="stToggle"] label *,
    div:has(.sim-toggle-container) [data-testid="stToggle"] p,
    div:has(.sim-toggle-container) [data-testid="stToggle"] span,
    div:has(.route-opt-panel-marker) [data-testid="stToggle"] label,
    div:has(.route-opt-panel-marker) [data-testid="stToggle"] label *,
    div:has(.route-opt-panel-marker) [data-testid="stToggle"] p,
    div:has(.route-opt-panel-marker) [data-testid="stToggle"] span,
    div:has(.route-opt-panel-marker) [data-testid="stToggle"] [data-testid="stWidgetLabel"],
    div:has(.route-opt-panel-marker) [data-testid="stToggle"] [data-testid="stWidgetLabel"] *,
    div:has(.route-opt-panel-marker) [data-testid="stToggle"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-testid="stToggle"] label,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-testid="stToggle"] label *,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-testid="stToggle"] label p,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-testid="stToggle"] label span,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-testid="stToggle"] [data-testid="stWidgetLabel"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-testid="stToggle"] [data-testid="stWidgetLabel"] *,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-baseweb="checkbox"] label,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-baseweb="checkbox"] span,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-baseweb="checkbox"] p,
    div:has(.sim-toggle-container) [data-baseweb="checkbox"] label,
    div:has(.sim-toggle-container) [data-baseweb="checkbox"] span,
    div:has(.sim-toggle-container) [data-baseweb="checkbox"] p,
    div:has(.sim-toggle-container) [data-baseweb="checkbox"] div:last-child * {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        opacity: 1 !important;
    }

    /* Selectbox inside the panel */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-testid="stSelectbox"] label,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-testid="stSelectbox"] label p,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-testid="stSelectbox"] label span,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-testid="stSelectbox"] [data-testid="stWidgetLabel"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] p,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] span {
        color: #38BDF8 !important;
        -webkit-text-fill-color: #38BDF8 !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        margin-bottom: 6px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-baseweb="select"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-baseweb="select"] > div {
        background: #031D3B !important;
        background-color: #031D3B !important;
        border: 1px solid rgba(32, 196, 255, 0.35) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        min-height: 42px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-baseweb="select"] > div:hover,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-baseweb="select"] > div:focus-within {
        border-color: rgba(32, 196, 255, 0.70) !important;
        box-shadow: 0 0 10px rgba(32, 196, 255, 0.25) !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-baseweb="select"] span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-opt-panel-marker) [data-baseweb="select"] svg {
        fill: #38BDF8 !important;
    }

    /* 4-Column Route Metrics Row */
    .route-metrics-row {
        display: grid !important;
        grid-template-columns: 1.35fr 1.15fr 1fr 1fr !important;
        gap: 0 !important;
        width: 100% !important;
        padding: 8px 0 !important;
        align-items: center !important;
    }

    @media (max-width: 900px) {
        .route-metrics-row {
            grid-template-columns: 1fr 1fr !important;
            row-gap: 16px !important;
        }
    }

    @media (max-width: 600px) {
        .route-metrics-row {
            grid-template-columns: 1fr !important;
            row-gap: 16px !important;
        }
    }

    .route-metric-col {
        display: flex !important;
        align-items: center !important;
        gap: 14px !important;
        padding: 6px 20px !important;
        border-right: 1px solid rgba(32, 196, 255, 0.18) !important;
        box-sizing: border-box !important;
    }

    .route-metric-col:first-child {
        padding-left: 0 !important;
    }

    .route-metric-col:last-child {
        border-right: none !important;
    }

    .route-metric-icon {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
    }

    .route-metric-info {
        display: flex !important;
        flex-direction: column !important;
    }

    .route-metric-label {
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.80rem !important;
        color: #38BDF8 !important;
        font-weight: 600 !important;
        margin-bottom: 3px !important;
        white-space: nowrap !important;
    }

    .route-metric-val {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        line-height: 1.15 !important;
    }

    .route-metric-route-text {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
        line-height: 1.35 !important;
    }

    /* Expander styling inside route panel */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-rec-panel-marker) [data-testid="stExpander"] {
        background: rgba(3, 29, 59, 0.60) !important;
        border: 1px solid rgba(32, 196, 255, 0.25) !important;
        border-radius: 8px !important;
        margin-top: 6px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-rec-panel-marker) [data-testid="stExpander"] details summary {
        color: rgba(255, 255, 255, 0.85) !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.90rem !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-rec-panel-marker) [data-testid="stExpander"] details summary svg {
        fill: #38BDF8 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.route-rec-panel-marker) [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        color: rgba(255, 255, 255, 0.80) !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.88rem !important;
        line-height: 1.5 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ---------------------------------------------------------
    # PANEL 1 — AI DYNAMIC ROUTE OPTIMIZATION ONLY
    # ---------------------------------------------------------
    with st.container(border=True):
        st.markdown(h("""
        <div class="route-opt-panel-marker"></div>
        <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;">
            AI Dynamic Route Optimization
        </div>
        <div style="font-family: 'Outfit', sans-serif; font-size: 0.90rem; color: rgba(255, 255, 255, 0.75); margin-bottom: 18px;">
            Simulate a corridor disruption and observe how the logistics network dynamically selects an alternative route.
        </div>
        """), unsafe_allow_html=True)
        
        simulation_col1, simulation_col2 = st.columns([1.5, 1.5])
        
        with simulation_col1:
            st.markdown('<div class="sim-toggle-container"></div>', unsafe_allow_html=True)
            simulate_closure = st.toggle(
                "Simulate Corridor A Closure",
                value=False,
                key="route_sim_closure_toggle"
            )
        
        with simulation_col2:
            vehicle_choice = st.selectbox(
                "Vehicle",
                ["V03 — Essential Medicine", "V01 — Food Supplies", "V02 — Construction Material"],
                key="route_vehicle_select"
            )
    
    # ---------------------------------------------------------
    # AI DYNAMIC ROUTE OPTIMIZATION ENGINE (SHARED ROAD STATUS)
    # ---------------------------------------------------------

    # 1. Fetch Authoritative Corridor Status (Shared with Home & GIS Fleet)
    try:
        gis_df, _tbl_df, _meta = get_authoritative_corridor_status()
    except Exception:
        gis_df, _tbl_df, _meta = get_static_fallback_corridors()

    # Map corridor status from shared provider
    corridor_status_map = {}
    for _, row in gis_df.iterrows():
        c_name = row.get("name", "")
        for char in ["A", "B", "C", "D", "E", "F", "G"]:
            if f"Corridor {char}" in c_name:
                st_text = str(row.get("status", "SAFE")).upper()
                corridor_status_map[char] = {
                    "status": st_text,
                    "color": row.get("color"),
                    "advisory": row.get("advisory", "")
                }
                break

    # 2. Vehicle Configuration & Delivery Priorities
    VEHICLES_CONFIG = {
        "V03 — Essential Medicine": {
            "id": "V03",
            "name": "Vehicle V03",
            "cargo": "Essential Medicine",
            "priority": "HIGH",
            "priority_label": "Critical / High Priority",
            "time_weight": 0.30,
            "dist_weight": 0.10,
            "risk_weight": 0.60
        },
        "V01 — Food Supplies": {
            "id": "V01",
            "name": "Vehicle V01",
            "cargo": "Food Supplies",
            "priority": "MEDIUM",
            "priority_label": "Perishable / Medium Priority",
            "time_weight": 0.45,
            "dist_weight": 0.25,
            "risk_weight": 0.30
        },
        "V02 — Construction Material": {
            "id": "V02",
            "name": "Vehicle V02",
            "cargo": "Construction Material",
            "priority": "LOW",
            "priority_label": "Economical / Bulk Freight",
            "time_weight": 0.15,
            "dist_weight": 0.60,
            "risk_weight": 0.25
        }
    }

    # 3. Route Candidates Connecting Guwahati to Imphal
    CANDIDATE_ROUTES = [
        {
            "id": "route_1_southern",
            "name": "Southern Arterial (Corridor A + C)",
            "path": ["Guwahati", "Shillong", "Silchar", "Imphal"],
            "display_str": "Guwahati → Shillong → Silchar → Imphal",
            "corridors": ["A", "C"],
            "distance": 560,
            "base_time_hours": 10.0,
            "base_risk": 20.0,
            "uses_corridor_a": True
        },
        {
            "id": "route_2_central",
            "name": "Central Express Arterial (Corridor E + D + NH-2)",
            "path": ["Guwahati", "Dimapur", "Kohima", "Imphal"],
            "display_str": "Guwahati → Dimapur → Kohima → Imphal",
            "corridors": ["E", "D"],
            "distance": 714,
            "base_time_hours": 12.0,
            "base_risk": 28.0,
            "uses_corridor_a": False
        },
        {
            "id": "route_3_northern",
            "name": "Northern Brahmaputra Arterial (Corridor B + D + NH-2)",
            "path": ["Guwahati", "Tezpur", "Dimapur", "Kohima", "Imphal"],
            "display_str": "Guwahati → Tezpur → Dimapur → Kohima → Imphal",
            "corridors": ["B", "D"],
            "distance": 699,
            "base_time_hours": 13.5,
            "base_risk": 19.0,
            "uses_corridor_a": False
        },
        {
            "id": "route_4_valley",
            "name": "Central Lumding Valley Bypass (Corridor E + Lumding + C)",
            "path": ["Guwahati", "Lumding", "Silchar", "Imphal"],
            "display_str": "Guwahati → Lumding → Silchar → Imphal",
            "corridors": ["E", "C"],
            "distance": 635,
            "base_time_hours": 11.5,
            "base_risk": 45.0,
            "uses_corridor_a": False
        },
        {
            "id": "route_5_highland",
            "name": "Highland Arterial (Corridor A + Kohima)",
            "path": ["Guwahati", "Shillong", "Kohima", "Imphal"],
            "display_str": "Guwahati → Shillong → Kohima → Imphal",
            "corridors": ["A", "D"],
            "distance": 640,
            "base_time_hours": 14.0,
            "base_risk": 28.0,
            "uses_corridor_a": True
        }
    ]

    # 4. Multi-Factor Optimization Engine
    max_time = 15.0
    max_dist = 800.0

    vehicle_results = {}
    for v_key, v_info in VEHICLES_CONFIG.items():
        w_time = v_info["time_weight"]
        w_dist = v_info["dist_weight"]
        w_risk = v_info["risk_weight"]

        candidates_scored = []
        for route in CANDIDATE_ROUTES:
            # When disruption is simulated, Corridor A routes are eliminated
            if simulate_closure and route["uses_corridor_a"]:
                continue

            eff_risk = route["base_risk"]

            # Incorporate live corridor status adjustments from TomTom provider
            for c_id in route["corridors"]:
                c_info = corridor_status_map.get(c_id, {})
                c_st = c_info.get("status", "")
                if "DANGER" in c_st or "HIGH RISK" in c_st:
                    eff_risk = max(eff_risk, 60.0)
                elif "MEDIUM" in c_st or "CAUTION" in c_st:
                    eff_risk = max(eff_risk, 35.0)

            # Determine Risk Level and Color
            if eff_risk < 25:
                risk_level = "Low"
                risk_color = "#10B981"
            elif eff_risk < 35:
                risk_level = "Medium"
                risk_color = "#38BDF8"
            elif eff_risk < 55:
                risk_level = "Moderate"
                risk_color = "#EAB308"
            else:
                risk_level = "High"
                risk_color = "#FB7185"

            # Weighted normalized cost score (lower is better)
            norm_time = route["base_time_hours"] / max_time
            norm_dist = route["distance"] / max_dist
            norm_risk = eff_risk / 100.0

            cost_score = (w_time * norm_time) + (w_dist * norm_dist) + (w_risk * norm_risk)

            candidates_scored.append({
                "id": route["id"],
                "name": route["name"],
                "display_str": route["display_str"],
                "distance": route["distance"],
                "travel_hours": route["base_time_hours"],
                "effective_risk": eff_risk,
                "risk_level": risk_level,
                "risk_color": risk_color,
                "cost_score": cost_score
            })

        if candidates_scored:
            candidates_scored.sort(key=lambda x: x["cost_score"])
            vehicle_results[v_key] = candidates_scored[0]
        else:
            vehicle_results[v_key] = None

    selected_opt = vehicle_results.get(vehicle_choice)

    if selected_opt:
        route_display_str = selected_opt["display_str"]
        travel_hours = selected_opt["travel_hours"]
        risk_level = selected_opt["risk_level"]
        risk_color = selected_opt["risk_color"]
        total_distance = selected_opt["distance"]

        # -----------------------------------------------------
        # PANEL 2 — RECOMMENDED ROUTE
        # -----------------------------------------------------
        with st.container(border=True):
            rec_panel_html = f"""
            <div class="route-rec-panel-marker"></div>
            <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;">
                Recommended Route
            </div>
            <div style="font-family: 'Outfit', sans-serif; font-size: 0.90rem; color: rgba(255, 255, 255, 0.75); margin-bottom: 18px;">
                View the AI-recommended optimal route based on current conditions, risk level, and delivery priorities.
            </div>
            <div class="route-metrics-row">
                <div class="route-metric-col">
                    <div class="route-metric-icon">
                        <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                            <path d="M12 2C8.13401 2 5 5.13401 5 9C5 14.25 12 22 12 22C12 22 19 14.25 19 9C19 5.13401 15.866 2 12 2Z" fill="#F43F5E" fill-opacity="0.3" stroke="#F43F5E" stroke-width="2"/>
                            <circle cx="12" cy="9" r="2.5" fill="#38BDF8"/>
                        </svg>
                    </div>
                    <div class="route-metric-route-text">{route_display_str}</div>
                </div>
                <div class="route-metric-col">
                    <div class="route-metric-icon">
                        <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
                            <circle cx="12" cy="12" r="9" stroke="#38BDF8" stroke-width="2.2" stroke-linecap="round"/>
                            <path d="M12 7V12L15.5 14" stroke="#38BDF8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <div class="route-metric-info">
                        <div class="route-metric-label">Estimated Delivery Time</div>
                        <div class="route-metric-val" style="color: #FFFFFF;">{travel_hours:.1f} hrs</div>
                    </div>
                </div>
                <div class="route-metric-col">
                    <div class="route-metric-icon">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                            <path d="M12 3L2 21H22L12 3Z" fill="#EAB308"/>
                            <path d="M12 9V14" stroke="#062B55" stroke-width="2" stroke-linecap="round"/>
                            <circle cx="12" cy="17.5" r="1.2" fill="#062B55"/>
                        </svg>
                    </div>
                    <div class="route-metric-info">
                        <div class="route-metric-label">Estimated Risk</div>
                        <div class="route-metric-val" style="color: {risk_color};">{risk_level}</div>
                    </div>
                </div>
                <div class="route-metric-col">
                    <div class="route-metric-icon">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                            <path d="M6 21L9.5 3H14.5L18 21" stroke="#38BDF8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M12 6V9M12 12V15M12 18V21" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <div class="route-metric-info">
                        <div class="route-metric-label">Total Distance</div>
                        <div class="route-metric-val" style="color: #FFFFFF;">{total_distance} km</div>
                    </div>
                </div>
            </div>
            <div style="border-top: 1px solid rgba(32, 196, 255, 0.18); margin: 16px 0 14px 0;"></div>
            """
            st.markdown(h(rec_panel_html), unsafe_allow_html=True)

            # -----------------------------------------------------
            # DECISION MESSAGE
            # -----------------------------------------------------
            if simulate_closure:
                status_html = f"""
                <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; font-family: 'Outfit', sans-serif;">
                    <div style="display: flex; align-items: center; gap: 10px; color: #FB7185; font-size: 0.94rem; font-weight: 500;">
                        <span style="display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: #FB7185; box-shadow: 0 0 8px #FB7185; flex-shrink: 0;"></span>
                        <span>Corridor A is unavailable. The route optimization engine has recalculated an alternative path through the active network.</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; color: #38BDF8; font-size: 0.94rem; font-weight: 500; margin-left: 19px;">
                        <span>Recommended action: Reroute {vehicle_choice} through {route_display_str}.</span>
                    </div>
                </div>
                """
                st.markdown(h(status_html), unsafe_allow_html=True)
            else:
                status_html = f"""
                <div style="display: flex; align-items: center; gap: 10px; font-family: 'Outfit', sans-serif; font-size: 0.94rem; color: #10B981; font-weight: 500; margin-bottom: 14px;">
                    <span style="display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: #10B981; box-shadow: 0 0 8px #10B981; flex-shrink: 0;"></span>
                    <span>Normal network condition. Recommended route: {route_display_str}</span>
                </div>
                """
                st.markdown(h(status_html), unsafe_allow_html=True)

            with st.expander("How the prototype routing engine works"):
                st.write(
                    """
                    The AI Dynamic Route Optimization engine evaluates multi-factor cost
                    functions independently for each vehicle in the fleet. Candidate routes
                    are generated across the 7 regional arterial corridors and connecting
                    highways.

                    Each candidate route is scored using a transparent weighted function
                    incorporating:
                    - Current road conditions & live TomTom Traffic incident/flow statuses
                    - Estimated transit travel time along the specific corridor profile
                    - Total route distance and fuel haulage efficiency
                    - Vehicle cargo sensitivity and delivery priority (Critical Medical,
                      Perishable Food, or Economical Bulk Freight)

                    When Corridor A closure is simulated, affected routes are eliminated
                    from consideration, and the engine calculates the lowest-cost valid
                    alternative tailored specifically to that vehicle's mission requirements.
                    """
                )

    else:
        with st.container(border=True):
            error_html = """
            <div class="route-rec-panel-marker"></div>
            <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;">
                Recommended Route
            </div>
            <div style="display: flex; align-items: center; gap: 10px; font-family: 'Outfit', sans-serif; font-size: 0.94rem; color: #FB7185; font-weight: 500; margin-top: 14px;">
                <span style="display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: #FB7185; box-shadow: 0 0 8px #FB7185; flex-shrink: 0;"></span>
                <span>No accessible route is currently available between the selected origin and destination.</span>
            </div>
            """
            st.markdown(h(error_html), unsafe_allow_html=True)

    
    # ---------------------------------------------------------
    # FOOTER
    # ---------------------------------------------------------
    
    st.divider()
    
    st.caption(
        "NER Logistics Accessibility Intelligence • SIH 2026 Prototype"
    )
    
    # ============================================================

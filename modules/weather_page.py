import streamlit as st
import pandas as pd
import pydeck as pdk
import folium
from streamlit_folium import st_folium
import networkx as nx
import requests
from streamlit_geolocation import streamlit_geolocation

def render_weather_page():
    # PART 3 — WEATHER + DISASTER SIMULATION + AI REROUTING
    # ============================================================
    
    st.markdown('<div id="weather-section"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    /* ============================================================
       WEATHER AI PAGE CONTAINMENT
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

    /* WEATHER PANELS — SOLID OPAQUE DARK NAVY (#062B55) */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.weather-panel-marker),
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:has(.weather-panel-marker),
    .block-container > div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stElementContainer"] .weather-panel-marker),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .weather-panel-marker) {
        background: #062B55 !important;
        background-color: #062B55 !important;
        opacity: 1 !important;
        border: 1px solid rgba(32, 196, 255, 0.45) !important;
        border-radius: 13px !important;
        padding: 20px 28px !important;
        margin: 0 auto 18px auto !important;
        max-width: 1060px !important;
        width: 100% !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.60), inset 0 0 16px rgba(32, 196, 255, 0.08) !important;
        transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.weather-panel-marker) > div,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.weather-panel-marker) > div[data-testid="stVerticalBlock"] {
        background: #062B55 !important;
        background-color: #062B55 !important;
        opacity: 1 !important;
        border: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.weather-panel-marker):hover,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .weather-panel-marker):hover {
        border-color: rgba(32, 196, 255, 0.70) !important;
        box-shadow: 0 12px 34px rgba(0, 0, 0, 0.70), inset 0 0 20px rgba(32, 196, 255, 0.12), 0 0 14px rgba(32, 196, 255, 0.25) !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.weather-panel-marker) div[data-testid="stVerticalBlock"]:not(:has(> div[data-testid="stElementContainer"] .weather-panel-marker)),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .weather-panel-marker) div[data-testid="stVerticalBlock"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.weather-panel-marker) div[data-testid="stElementContainer"],
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .weather-panel-marker) div[data-testid="stElementContainer"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 3-Column Weather Metrics Row */
    .weather-metrics-row {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 0 !important;
        width: 100% !important;
        padding: 6px 0 !important;
    }

    @media (max-width: 768px) {
        .weather-metrics-row {
            grid-template-columns: 1fr !important;
            row-gap: 16px !important;
        }
    }

    .weather-metric-col {
        display: flex !important;
        align-items: center !important;
        gap: 14px !important;
        padding: 6px 28px !important;
        border-right: 1px solid rgba(32, 196, 255, 0.18) !important;
        box-sizing: border-box !important;
    }

    .weather-metric-col:first-child {
        padding-left: 0 !important;
    }

    .weather-metric-col:last-child {
        border-right: none !important;
    }

    .weather-metric-icon {
        font-size: 1.8rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
    }

    .weather-metric-info {
        display: flex !important;
        flex-direction: column !important;
    }

    .weather-metric-label {
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.82rem !important;
        color: #38BDF8 !important;
        font-weight: 500 !important;
        margin-bottom: 4px !important;
        white-space: nowrap !important;
    }

    .weather-metric-val {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        line-height: 1.15 !important;
    }

    /* Simulation Button Styling: Red background/border + Black text + Centered + Slightly narrower than panel */
    div[data-testid="stVerticalBlock"]:has(.weather-sim-panel) .stButton {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
        margin-top: 6px !important;
    }

    div[data-testid="stVerticalBlock"]:has(.weather-sim-panel) .stButton > button {
        background: #DC2626 !important;
        background-color: #DC2626 !important;
        border: 2px solid #EF4444 !important;
        border-radius: 12px !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.98rem !important;
        padding: 11px 28px !important;
        max-width: 480px !important;
        width: 100% !important;
        margin: 0 auto !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 8px !important;
        box-shadow: 0 4px 18px rgba(220, 38, 38, 0.45) !important;
        transition: all 0.25s ease !important;
    }

    div[data-testid="stVerticalBlock"]:has(.weather-sim-panel) .stButton > button:hover {
        background: #EF4444 !important;
        background-color: #EF4444 !important;
        border-color: #F87171 !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        box-shadow: 0 6px 24px rgba(239, 68, 68, 0.65) !important;
        transform: translateY(-1px) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ------------------------------------------------------------
    # Weather data
    # ------------------------------------------------------------
    
    @st.cache_data(ttl=600)
    def get_weather():
        try:
            url = (
                "https://api.open-meteo.com/v1/forecast"
                "?latitude=26.1445"
                "&longitude=91.7362"
                "&current=temperature_2m,precipitation,wind_speed_10m"
            )
    
            response = requests.get(url, timeout=5)
    
            if response.status_code == 200:
                data = response.json()
    
                return {
                    "temperature": data["current"]["temperature_2m"],
                    "rainfall": data["current"]["precipitation"],
                    "wind": data["current"]["wind_speed_10m"]
                }
    
        except Exception:
            pass
    
        return {
            "temperature": 27.0,
            "rainfall": 18.5,
            "wind": 14.0
        }
    
    weather = get_weather()
    
    # ------------------------------------------------------------
    # PANEL 1 — WEATHER & DISASTER INTELLIGENCE
    # ------------------------------------------------------------
    with st.container(border=True):
        st.markdown(f'''
        <div class="weather-panel-marker"></div>
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
            <span style="font-size: 1.35rem;">🌧️</span>
            <span style="font-family: 'Outfit', sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF;">Weather & Disaster Intelligence</span>
        </div>
        <div style="font-family: 'Outfit', sans-serif; font-size: 0.90rem; color: rgba(255, 255, 255, 0.75); margin-bottom: 20px;">Prototype simulation showing how weather and infrastructure disruptions can trigger dynamic logistics rerouting.</div>
        <div class="weather-metrics-row">
            <div class="weather-metric-col">
                <div class="weather-metric-icon">🌡️</div>
                <div class="weather-metric-info">
                    <div class="weather-metric-label">Temperature</div>
                    <div class="weather-metric-val" style="color: #FFFFFF;">{weather['temperature']} °C</div>
                </div>
            </div>
            <div class="weather-metric-col">
                <div class="weather-metric-icon">🌧️</div>
                <div class="weather-metric-info">
                    <div class="weather-metric-label">Rainfall</div>
                    <div class="weather-metric-val" style="color: #C084FC;">{weather['rainfall']} mm</div>
                </div>
            </div>
            <div class="weather-metric-col">
                <div class="weather-metric-icon">💨</div>
                <div class="weather-metric-info">
                    <div class="weather-metric-label">Wind</div>
                    <div class="weather-metric-val" style="color: #FFFFFF;">{weather['wind']} km/h</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    # ------------------------------------------------------------
    # PANEL 2 — SIMULATE HEAVY RAINFALL + ROAD CLOSURE
    # ------------------------------------------------------------
    with st.container(border=True):
        st.markdown('''
        <div class="weather-panel-marker weather-sim-panel"></div>
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" style="vertical-align: middle; flex-shrink: 0;">
                <rect width="24" height="24" rx="6" fill="#EF4444"/>
                <path d="M4 20L20 4M2 14L14 2M10 22L22 10" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
            <span style="font-family: 'Outfit', sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF;">Simulate Heavy Rainfall + Road Closure</span>
        </div>
        <div style="font-family: 'Outfit', sans-serif; font-size: 0.90rem; color: rgba(255, 255, 255, 0.75); margin-bottom: 20px;">Use the simulation to demonstrate how the system reacts when a critical logistics corridor becomes inaccessible.</div>
        ''', unsafe_allow_html=True)
        
        simulate_disaster = st.button(
            "⚠️ Simulate Heavy Rainfall + Road Closure",
            use_container_width=True,
            key="simulate_disaster_btn"
        )
    
    if simulate_disaster:
        st.session_state["disaster_active"] = True
    
    if "disaster_active" not in st.session_state:
        st.session_state["disaster_active"] = False
    
    
    # ------------------------------------------------------------
    # Route network
    # ------------------------------------------------------------
    
    G = nx.Graph()
    
    # Nodes represent logistics locations
    G.add_node("Guwahati")
    G.add_node("Silchar")
    G.add_node("Imphal")
    G.add_node("Shillong")
    G.add_node("Aizawl")
    
    # Normal network
    G.add_edge("Guwahati", "Silchar", weight=6)
    G.add_edge("Silchar", "Imphal", weight=8)
    G.add_edge("Guwahati", "Imphal", weight=10)
    G.add_edge("Guwahati", "Shillong", weight=4)
    G.add_edge("Shillong", "Imphal", weight=9)
    G.add_edge("Silchar", "Aizawl", weight=5)
    
    # ------------------------------------------------------------
    # Normal route
    # ------------------------------------------------------------
    
    source = "Guwahati"
    destination = "Imphal"
    
    normal_route = nx.shortest_path(
        G,
        source=source,
        target=destination,
        weight="weight"
    )
    
    normal_distance = nx.shortest_path_length(
        G,
        source=source,
        target=destination,
        weight="weight"
    )
    
    
    # ------------------------------------------------------------
    # Disaster scenario
    # ------------------------------------------------------------
    
    if st.session_state["disaster_active"]:
    
        st.error(
            "🚨 CRITICAL DISRUPTION DETECTED — "
            "Silchar → Imphal corridor is inaccessible."
        )
    
        st.warning(
            "Heavy rainfall has increased landslide risk. "
            "The primary corridor has been temporarily blocked."
        )
    
        # Remove affected corridor
        if G.has_edge("Silchar", "Imphal"):
            G.remove_edge("Silchar", "Imphal")
    
        # Calculate alternate route
        alternate_route = nx.shortest_path(
            G,
            source=source,
            target=destination,
            weight="weight"
        )
    
        alternate_distance = nx.shortest_path_length(
            G,
            source=source,
            target=destination,
            weight="weight"
        )
    
        delay = alternate_distance - normal_distance
    
        st.markdown("### 🤖 AI Dynamic Route Optimization")
    
        col1, col2 = st.columns(2)
    
        with col1:
            st.info(
                f"""
                **Original Route**
    
                {' → '.join(normal_route)}
    
                Estimated Distance:
                **{normal_distance} units**
                """
            )
    
        with col2:
            st.success(
                f"""
                **Recommended Alternate Route**
    
                {' → '.join(alternate_route)}
    
                Estimated Distance:
                **{alternate_distance} units**
                """
            )
    
        st.metric(
            "⏱️ Estimated Additional Delay",
            f"+{delay} distance units"
        )
    
        st.success(
            f"🔄 Recommendation: Reroute essential-cargo vehicles "
            f"from {source} to {destination} through the alternate corridor."
        )
    
        # --------------------------------------------------------
        # Impact analysis
        # --------------------------------------------------------
    
        st.markdown("### 📊 Disruption Impact Analysis")
    
        impact = pd.DataFrame([
            {
                "Impact": "Primary Corridor",
                "Status": "🔴 BLOCKED",
                "Value": "Silchar → Imphal"
            },
            {
                "Impact": "Vehicle V03",
                "Status": "⚠️ AFFECTED",
                "Value": "Medicine Cargo"
            },
            {
                "Impact": "Alternate Route",
                "Status": "🟢 AVAILABLE",
                "Value": "AI Recommended"
            },
            {
                "Impact": "Delivery",
                "Status": "⚠️ DELAYED",
                "Value": f"+{delay} distance units"
            }
        ])
    
        st.dataframe(
            impact,
            use_container_width=True,
            hide_index=True
        )
    
    else:
    
        st.info(
            "🟢 Network operating under normal simulated conditions. "
            "Trigger the disaster scenario to demonstrate dynamic rerouting."
        )
    
    
    # ------------------------------------------------------------
    # Reset simulation
    # ------------------------------------------------------------
    
    if st.session_state["disaster_active"]:
    
        if st.button(
            "↩️ Reset Disaster Simulation",
            use_container_width=True
        ):
            st.session_state["disaster_active"] = False
            st.rerun()
      
      # ============================================================


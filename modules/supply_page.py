import streamlit as st
import pandas as pd
import pydeck as pdk
import folium
from streamlit_folium import st_folium
import networkx as nx
import requests
from streamlit_geolocation import streamlit_geolocation

def render_supply_page():
    # PART 4 — SUPPLY CONTINUITY INTELLIGENCE
    # ============================================================
    
    st.markdown('<div id="supply-section"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin: 1.75rem auto 1.5rem auto; max-width: 850px; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;">
        <h2 style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.75rem; font-weight: 700; color: #FFFFFF; margin: 0 0 0.45rem 0; text-align: center; line-height: 1.25; letter-spacing: -0.01em;">Supply Continuity Intelligence</h2>
        <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 0.95rem; font-weight: 400; color: rgba(255, 255, 255, 0.85); text-align: center; line-height: 1.55; max-width: 680px; margin: 0 auto;">Prototype decision-support model estimating whether essential supplies may be disrupted by logistics conditions.</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ------------------------------------------------------------
    # Simulated district supply data
    # ------------------------------------------------------------
    
    supply_data = pd.DataFrame([
        {
            "District": "Imphal",
            "Essential Item": "Medicine",
            "Stock Remaining": 14,
            "Incoming ETA": 8,
            "Road Risk": 82,
            "Population Dependency": "High"
        },
        {
            "District": "Shillong",
            "Essential Item": "Food Supplies",
            "Stock Remaining": 30,
            "Incoming ETA": 5,
            "Road Risk": 21,
            "Population Dependency": "Medium"
        },
        {
            "District": "Aizawl",
            "Essential Item": "Construction Material",
            "Stock Remaining": 26,
            "Incoming ETA": 7,
            "Road Risk": 38,
            "Population Dependency": "Medium"
        },
        {
            "District": "Agartala",
            "Essential Item": "Medicine",
            "Stock Remaining": 20,
            "Incoming ETA": 6,
            "Road Risk": 25,
            "Population Dependency": "High"
        }
    ])
    
    # ============================================================
    # SUPPLY PANELS DESIGN SYSTEM & LAYOUT
    # ============================================================
    st.markdown("""
    <style>
    /* ============================================================
       SUPPLY & CARGO PAGE CONTAINMENT
       Guarantee that the page root block stays completely transparent
       and full width so the mountain background is 100% visible
       outside and between the panels, and the top navbar preserves
       its exact original full width, position, and layout.
       Zero page-level blue overlay or wrapper container.
       ============================================================ */
    .block-container > div[data-testid="stVerticalBlock"] {
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        border: none !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    /* ============================================================
       3 INDIVIDUAL PANELS ONLY — SOLID OPAQUE DARK NAVY (#062B55)
       Strictly scoped ONLY to each panel container.
       Both outer wrapper and inner container are solid #062B55 so
       zero mountain wallpaper can bleed through the panels.
       ============================================================ */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker),
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker),
    .block-container > div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stElementContainer"] .supply-panel-marker),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .supply-panel-marker) {
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

    /* Inner block of the bordered container: solid navy and border-none so the whole card is solid navy with 1 border */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) > div,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) > div[data-testid="stVerticalBlock"] {
        background: #062B55 !important;
        background-color: #062B55 !important;
        opacity: 1 !important;
        border: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker):hover,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .supply-panel-marker):hover {
        border-color: rgba(32, 196, 255, 0.70) !important;
        box-shadow: 0 12px 34px rgba(0, 0, 0, 0.70), inset 0 0 20px rgba(32, 196, 255, 0.12), 0 0 14px rgba(32, 196, 255, 0.25) !important;
    }

    /* Sub-blocks inside the panel (like columns) stay transparent */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) div[data-testid="stVerticalBlock"]:not(:has(> div[data-testid="stElementContainer"] .supply-panel-marker)),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .supply-panel-marker) div[data-testid="stVerticalBlock"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Element containers inside the panel stay transparent */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) div[data-testid="stElementContainer"],
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .supply-panel-marker) div[data-testid="stElementContainer"] {
        background: transparent !important;
        background-color: transparent !important;
    }

    /* Panel Header with Bottom Divider Line */
    .supply-panel-header {
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 1.18rem !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        padding-bottom: 12px !important;
        margin-bottom: 16px !important;
        border-bottom: 1px solid rgba(32, 196, 255, 0.20) !important;
        width: 100% !important;
    }

    .supply-panel-header .header-icon {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        color: #20C4FF !important;
        flex-shrink: 0 !important;
    }

    /* Selectbox Styling inside Panel 1 */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) label,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) label p,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) label span,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) [data-testid="stWidgetLabel"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) [data-testid="stWidgetLabel"] p,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) [data-testid="stWidgetLabel"] span {
        color: #94A3B8 !important;
        -webkit-text-fill-color: #94A3B8 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        margin-bottom: 6px !important;
    }

    /* Selectbox Container: Dark Navy Recessed Background + Subtle Blue Border */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) [data-baseweb="select"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) [data-baseweb="select"] > div {
        background: #031D3B !important;
        background-color: #031D3B !important;
        border: 1px solid rgba(32, 196, 255, 0.35) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        min-height: 44px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) [data-baseweb="select"] > div:hover,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) [data-baseweb="select"] > div:focus-within {
        border-color: rgba(32, 196, 255, 0.70) !important;
        box-shadow: 0 0 10px rgba(32, 196, 255, 0.25) !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) [data-baseweb="select"] input {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) [data-baseweb="select"] div,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) [data-baseweb="select"] span,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) [data-baseweb="select"] [data-testid="stMarkdownContainer"] p {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) [data-baseweb="select"] svg {
        color: #20C4FF !important;
        fill: #20C4FF !important;
        stroke: #20C4FF !important;
    }

    /* Popover dropdown menu items */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    ul[data-baseweb="menu"] {
        background: #031D3B !important;
        background-color: #031D3B !important;
        border: 1px solid rgba(32, 196, 255, 0.45) !important;
        border-radius: 8px !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.7) !important;
    }

    li[data-baseweb="menu-item"] {
        color: #FFFFFF !important;
        background-color: transparent !important;
        font-family: 'Outfit', sans-serif !important;
    }

    li[data-baseweb="menu-item"]:hover,
    li[data-baseweb="menu-item"][aria-selected="true"] {
        background-color: rgba(32, 196, 255, 0.20) !important;
        color: #20C4FF !important;
    }

    /* Button inside Supply Panels (e.g. Analyze Potential Impact) */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) .stButton,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .supply-panel-marker) .stButton {
        width: 100% !important;
        margin-top: 10px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) .stButton > button,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .supply-panel-marker) .stButton > button {
        background: rgba(3, 29, 59, 0.85) !important;
        background-color: rgba(3, 29, 59, 0.85) !important;
        border: 1px solid rgba(32, 196, 255, 0.45) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 10px 24px !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.2s ease !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.supply-panel-marker) .stButton > button:hover,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .supply-panel-marker) .stButton > button:hover {
        background: rgba(32, 196, 255, 0.20) !important;
        background-color: rgba(32, 196, 255, 0.20) !important;
        border-color: #20C4FF !important;
        box-shadow: 0 0 16px rgba(32, 196, 255, 0.35) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Panel 2: 4 Horizontally Arranged Metrics with Vertical Dividers */
    .supply-metrics-row {
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important;
        gap: 0 !important;
        width: 100% !important;
        padding: 6px 0 !important;
    }

    @media (max-width: 880px) {
        .supply-metrics-row {
            grid-template-columns: repeat(2, 1fr) !important;
            row-gap: 16px !important;
        }
    }

    @media (max-width: 480px) {
        .supply-metrics-row {
            grid-template-columns: 1fr !important;
            row-gap: 14px !important;
        }
    }

    .supply-metric-col {
        display: flex !important;
        align-items: center !important;
        gap: 14px !important;
        padding: 8px 22px !important;
        border-right: 1px solid rgba(32, 196, 255, 0.18) !important;
        box-sizing: border-box !important;
    }

    .supply-metric-col:first-child {
        padding-left: 4px !important;
    }

    .supply-metric-col:last-child {
        border-right: none !important;
    }

    .supply-metric-icon {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
    }

    .supply-metric-info {
        display: flex !important;
        flex-direction: column !important;
    }

    .supply-metric-label {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 0.82rem !important;
        color: #94A3B8 !important;
        font-weight: 500 !important;
        margin-bottom: 3px !important;
        white-space: nowrap !important;
    }

    .supply-metric-value {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 1.65rem !important;
        font-weight: 800 !important;
        line-height: 1.1 !important;
    }

    /* Panel 3: Supply Continuity Assessment Layout */
    .supply-assessment-row {
        display: grid !important;
        grid-template-columns: 1.1fr 1.1fr 1.3fr !important;
        gap: 0 !important;
        width: 100% !important;
        padding: 6px 0 !important;
    }

    @media (max-width: 768px) {
        .supply-assessment-row {
            grid-template-columns: 1fr !important;
            row-gap: 16px !important;
        }
    }

    .supply-assessment-col {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        padding: 6px 24px !important;
        border-right: 1px solid rgba(32, 196, 255, 0.18) !important;
        box-sizing: border-box !important;
    }

    .supply-assessment-col:first-child {
        padding-left: 4px !important;
    }

    .supply-assessment-badge-col {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-right: none !important;
    }

    .supply-assessment-label {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 0.82rem !important;
        color: #94A3B8 !important;
        font-weight: 500 !important;
        margin-bottom: 4px !important;
    }

    .supply-assessment-value {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        line-height: 1.1 !important;
    }

    .supply-risk-badge {
        display: inline-flex !important;
        align-items: center !important;
        gap: 10px !important;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
    }

    .supply-risk-dot {
        width: 11px !important;
        height: 11px !important;
        border-radius: 50% !important;
        flex-shrink: 0 !important;
        display: inline-block !important;
    }

    .supply-action-box {
        display: flex !important;
        align-items: flex-start !important;
        gap: 12px !important;
        margin-top: 18px !important;
        padding-top: 16px !important;
        border-top: 1px solid rgba(32, 196, 255, 0.15) !important;
        width: 100% !important;
    }

    .supply-action-icon {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
        margin-top: 2px !important;
    }

    .supply-action-text {
        display: flex !important;
        flex-direction: column !important;
        gap: 3px !important;
    }

    .supply-action-title {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 0.94rem !important;
        font-weight: 700 !important;
        color: #38BDF8 !important;
        line-height: 1.4 !important;
    }

    .supply-action-desc {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        color: #7DD3FC !important;
        opacity: 0.92 !important;
        line-height: 1.4 !important;
    }

    /* Delivery Intelligence & Priority Factors 4-Column Row */
    .supply-cols-row {
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important;
        gap: 0 !important;
        width: 100% !important;
        padding: 4px 0 !important;
    }

    @media (max-width: 880px) {
        .supply-cols-row {
            grid-template-columns: repeat(2, 1fr) !important;
            row-gap: 16px !important;
        }
    }

    @media (max-width: 480px) {
        .supply-cols-row {
            grid-template-columns: 1fr !important;
            row-gap: 14px !important;
        }
    }

    .supply-col-item {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        padding: 4px 22px !important;
        border-right: 1px solid rgba(32, 196, 255, 0.18) !important;
        box-sizing: border-box !important;
    }

    .supply-col-item:first-child {
        padding-left: 0 !important;
    }

    .supply-col-item:last-child {
        border-right: none !important;
    }

    .supply-col-label {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 0.82rem !important;
        color: #38BDF8 !important;
        font-weight: 500 !important;
        margin-bottom: 6px !important;
        white-space: nowrap !important;
    }

    .supply-col-val {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        line-height: 1.15 !important;
    }

    /* AI Priority Assessment Split */
    .supply-assessment-split {
        display: grid !important;
        grid-template-columns: 240px 1fr !important;
        gap: 0 !important;
        width: 100% !important;
        padding: 4px 0 !important;
        align-items: center !important;
    }

    @media (max-width: 768px) {
        .supply-assessment-split {
            grid-template-columns: 1fr !important;
            row-gap: 16px !important;
        }
    }

    .supply-assessment-left {
        display: flex !important;
        flex-direction: column !important;
        padding: 4px 24px 4px 0 !important;
        border-right: 1px solid rgba(32, 196, 255, 0.18) !important;
        box-sizing: border-box !important;
    }

    .supply-assessment-right {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        padding: 4px 0 4px 28px !important;
        box-sizing: border-box !important;
    }

    /* Recommended Action Content */
    .supply-recommendation-content {
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 0.96rem !important;
        font-weight: 500 !important;
        color: #38BDF8 !important;
        line-height: 1.5 !important;
    }

    /* District Supply Overview Table Width & Alignment */
    .block-container > div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stElementContainer"] .supply-table-marker),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .supply-table-marker),
    div[data-testid="stElementContainer"]:has(.supply-table-marker),
    div[data-testid="stElementContainer"]:has(.supply-table-marker) ~ div[data-testid="stElementContainer"] {
        max-width: 1060px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }

    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .supply-table-marker) div[data-testid="stDataFrame"],
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .supply-table-marker) [data-testid="stDataFrame"] > div,
    div[data-testid="stElementContainer"]:has(.supply-table-marker) ~ div[data-testid="stElementContainer"] div[data-testid="stDataFrame"],
    div[data-testid="stElementContainer"]:has(.supply-table-marker) ~ div[data-testid="stElementContainer"] [data-testid="stDataFrame"] > div {
        max-width: 1060px !important;
        width: 100% !important;
    }

    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .supply-table-marker) h3,
    div[data-testid="stElementContainer"]:has(.supply-table-marker) ~ div[data-testid="stElementContainer"] h3 {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        color: #FFFFFF !important;
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        margin: 20px 0 12px 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------------
    # PANEL 1 — SELECT DISTRICT
    # ------------------------------------------------------------
    with st.container(border=True):
        st.markdown('''
        <div class="supply-panel-marker"></div>
        <div class="supply-panel-header">
            <span class="header-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#20C4FF" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                </svg>
            </span>
            <span>Select District</span>
        </div>
        ''', unsafe_allow_html=True)
        
        selected_district = st.selectbox(
            "Select District",
            supply_data["District"].tolist()
        )

    district_row = supply_data[
        supply_data["District"] == selected_district
    ].iloc[0]
    
    # ------------------------------------------------------------
    # Extract values
    # ------------------------------------------------------------
    stock_remaining = float(district_row["Stock Remaining"])
    incoming_eta = float(district_row["Incoming ETA"])
    road_risk = float(district_row["Road Risk"])
    dependency = district_row["Population Dependency"]
    
    # ------------------------------------------------------------
    # Dependency factor
    # ------------------------------------------------------------
    dependency_factor = {
        "Low": 0.7,
        "Medium": 0.85,
        "High": 1.0
    }
    dependency_multiplier = dependency_factor[dependency]
    
    # ------------------------------------------------------------
    # Supply continuity risk calculation
    # ------------------------------------------------------------
    stock_pressure = max(0, 1 - (stock_remaining / 48))
    eta_pressure = min(incoming_eta / 24, 1)
    road_pressure = road_risk / 100
    
    risk_score = (
        0.40 * road_pressure
        + 0.35 * eta_pressure
        + 0.25 * stock_pressure
    )
    risk_score = risk_score * dependency_multiplier
    risk_score = min(max(risk_score, 0), 1)
    
    supply_risk_percentage = round(risk_score * 100)
    supply_continuity_score = round(100 - supply_risk_percentage)
    
    # ------------------------------------------------------------
    # PANEL 2 — CURRENT SUPPLY SITUATION
    # ------------------------------------------------------------
    with st.container(border=True):
        st.markdown(f'''
        <div class="supply-panel-marker"></div>
        <div class="supply-panel-header">
            <span class="header-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#20C4FF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                    <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                    <line x1="12" y1="22.08" x2="12" y2="12"></line>
                </svg>
            </span>
            <span>Current Supply Situation</span>
        </div>
        <div class="supply-metrics-row">
            <div class="supply-metric-col">
                <div class="supply-metric-icon">
                    <svg width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                </div>
                <div class="supply-metric-info">
                    <div class="supply-metric-label">Stock Remaining</div>
                    <div class="supply-metric-value" style="color: #10B981;">{stock_remaining:.0f} hrs</div>
                </div>
            </div>
            <div class="supply-metric-col">
                <div class="supply-metric-icon">
                    <svg width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="15" height="13"></rect><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon><circle cx="5.5" cy="18.5" r="2.5"></circle><circle cx="18.5" cy="18.5" r="2.5"></circle></svg>
                </div>
                <div class="supply-metric-info">
                    <div class="supply-metric-label">Incoming ETA</div>
                    <div class="supply-metric-value" style="color: #F59E0B;">{incoming_eta:.0f} hrs</div>
                </div>
            </div>
            <div class="supply-metric-col">
                <div class="supply-metric-icon">
                    <svg width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="#FACC15" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                </div>
                <div class="supply-metric-info">
                    <div class="supply-metric-label">Road Risk</div>
                    <div class="supply-metric-value" style="color: #FACC15;">{road_risk:.0f}%</div>
                </div>
            </div>
            <div class="supply-metric-col" style="border-right: none;">
                <div class="supply-metric-icon">
                    <svg width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="#C084FC" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                </div>
                <div class="supply-metric-info">
                    <div class="supply-metric-label">Dependency</div>
                    <div class="supply-metric-value" style="color: #C084FC;">{dependency}</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    # ------------------------------------------------------------
    # PANEL 3 — SUPPLY CONTINUITY ASSESSMENT
    # ------------------------------------------------------------
    if supply_risk_percentage >= 75:
        risk_label = "CRITICAL SUPPLY RISK"
        risk_color = "#EF4444"
        risk_dot = "#EF4444"
        risk_msg = f"The {selected_district} supply chain may face a critical disruption for {district_row['Essential Item']}."
        action_msg = "Recommended Action: Prioritize this delivery and reroute through the safest available corridor."
    elif supply_risk_percentage >= 50:
        risk_label = "HIGH SUPPLY RISK"
        risk_color = "#EF4444"
        risk_dot = "#EF4444"
        risk_msg = f"The {selected_district} supply chain is vulnerable to disruption."
        action_msg = "Recommended Action: Monitor the incoming vehicle and prepare an alternate route."
    elif supply_risk_percentage >= 30:
        risk_label = "MODERATE SUPPLY RISK"
        risk_color = "#F59E0B"
        risk_dot = "#F59E0B"
        risk_msg = "Supply continuity is currently manageable but should be monitored."
        action_msg = "Recommended Action: Maintain regular monitoring and verify stock levels."
    else:
        risk_label = "LOW SUPPLY RISK"
        risk_color = "#10B981"
        risk_dot = "#10B981"
        risk_msg = "Current logistics conditions indicate relatively stable supply continuity."
        action_msg = "Recommended Action: Standard operations continue."

    with st.container(border=True):
        st.markdown(f'''
        <div class="supply-panel-marker"></div>
        <div class="supply-panel-header">
            <span class="header-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#20C4FF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                </svg>
            </span>
            <span>Supply Continuity Assessment</span>
        </div>
        <div class="supply-assessment-row">
            <div class="supply-assessment-col">
                <div class="supply-assessment-label">Supply Continuity Score</div>
                <div class="supply-assessment-value" style="color: #20C4FF;">{supply_continuity_score}%</div>
            </div>
            <div class="supply-assessment-col">
                <div class="supply-assessment-label">Supply Disruption Risk</div>
                <div class="supply-assessment-value" style="color: #FACC15;">{supply_risk_percentage}%</div>
            </div>
            <div class="supply-assessment-col supply-assessment-badge-col" style="border-right: none;">
                <div class="supply-risk-badge" style="color: {risk_color};">
                    <span class="supply-risk-dot" style="background: {risk_dot}; box-shadow: 0 0 10px {risk_dot};"></span>
                    <span>{risk_label}</span>
                </div>
            </div>
        </div>
        <div class="supply-action-box">
            <div class="supply-action-icon">
                <svg width="19" height="19" viewBox="0 0 24 24" fill="#0284C7" stroke="#0284C7" stroke-width="1.5">
                    <circle cx="12" cy="12" r="10" fill="#0284C7"></circle>
                    <line x1="12" y1="16" x2="12" y2="11" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"></line>
                    <circle cx="12" cy="7.5" r="1" fill="#FFFFFF"></circle>
                </svg>
            </div>
            <div class="supply-action-text">
                <div class="supply-action-title">{risk_msg}</div>
                <div class="supply-action-desc">{action_msg}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    # ------------------------------------------------------------
    # Decision explanation
    # ------------------------------------------------------------
    
    with st.expander(
        "🔍 Why did the system produce this score?"
    ):
    
        st.write(
            f"""
            The prototype combines four factors:
    
            • Road disruption risk: {road_risk:.0f}%
    
            • Incoming vehicle ETA: {incoming_eta:.0f} hours
    
            • Remaining supply: {stock_remaining:.0f} hours
    
            • Population dependency: {dependency}
    
            Higher road risk, longer delivery ETA and lower remaining
            stock increase the probability of supply disruption.
    
            Population dependency increases the priority of districts
            where essential goods are more critical.
            """
        )
    
    # ------------------------------------------------------------
    # Supply overview table
    # ------------------------------------------------------------
    
    with st.container():
        st.markdown('''
        <div class="supply-table-marker"></div>
        <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin: 20px 0 12px 0;">District Supply Overview</div>
        ''', unsafe_allow_html=True)
        
        overview = supply_data.copy()
        
        overview["Risk Estimate"] = overview.apply(
            lambda row: (
                "🔴 Critical"
                if row["Road Risk"] >= 75
                else "🟠 High"
                if row["Road Risk"] >= 50
                else "🟡 Moderate"
                if row["Road Risk"] >= 30
                else "🟢 Low"
            ),
            axis=1
        )
        
        st.dataframe(
            overview[
                [
                    "District",
                    "Essential Item",
                    "Stock Remaining",
                    "Incoming ETA",
                    "Road Risk",
                    "Population Dependency",
                    "Risk Estimate"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )
        
    # ============================================================
    # PART 5 — IMPACT BEFORE INCIDENT ENGINE
    # ============================================================
    
    with st.container(border=True):
        st.markdown('''
        <div class="supply-panel-marker"></div>
        <div style="font-family: 'Outfit', sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;">Impact Before Incident</div>
        <div style="font-family: 'Outfit', sans-serif; font-size: 0.90rem; color: rgba(255, 255, 255, 0.75); margin-bottom: 16px;">Proactive decision-support simulation showing the potential logistics impact of a corridor failure before it occurs.</div>
        ''', unsafe_allow_html=True)
        
        impact_scenario = st.selectbox(
            "Select Potential Disruption",
            [
                "Heavy Rainfall — Corridor A",
                "Landslide Risk — Corridor B",
                "Flood Risk — Corridor C"
            ]
        )
        
        scenario_data = {
            "Heavy Rainfall — Corridor A": {
                "corridor": "Corridor A",
                "risk": 82,
                "vehicles": 3,
                "deliveries": 7,
                "districts": 2,
                "delay": 5,
                "supply_risk": 78,
                "commodity": "Medicine & Food"
            },
        
            "Landslide Risk — Corridor B": {
                "corridor": "Corridor B",
                "risk": 74,
                "vehicles": 2,
                "deliveries": 5,
                "districts": 2,
                "delay": 4,
                "supply_risk": 64,
                "commodity": "Medicine"
            },
        
            "Flood Risk — Corridor C": {
                "corridor": "Corridor C",
                "risk": 69,
                "vehicles": 4,
                "deliveries": 9,
                "districts": 3,
                "delay": 6,
                "supply_risk": 71,
                "commodity": "Food & Construction Material"
            }
        }
        
        scenario = scenario_data[impact_scenario]
        
        analyze_impact = st.button(
            "🔍 Analyze Potential Impact",
            use_container_width=True
        )
    
    if "analyze_impact_triggered" not in st.session_state:
        st.session_state["analyze_impact_triggered"] = False

    if analyze_impact:
        st.session_state["analyze_impact_triggered"] = True

    if st.session_state["analyze_impact_triggered"]:
        if scenario["supply_risk"] >= 75:
            risk_level_text = "Critical"
            risk_color = "#FB7185"
            recommendation = (
                f"Pre-position {scenario['commodity']} and "
                f"reroute high-priority vehicles before "
                f"{scenario['corridor']} becomes inaccessible."
            )
        elif scenario["supply_risk"] >= 50:
            risk_level_text = "High"
            risk_color = "#F59E0B"
            recommendation = (
                f"Monitor {scenario['corridor']} closely and "
                f"prepare alternate routes for essential cargo."
            )
        else:
            risk_level_text = "Moderate"
            risk_color = "#10B981"
            recommendation = (
                f"Continue monitoring {scenario['corridor']} "
                f"and maintain normal logistics operations."
            )

        # ------------------------------------------------------------
        # 1. Predicted Logistics Impact Panel
        # ------------------------------------------------------------
        with st.container(border=True):
            st.markdown(f'''
            <div class="supply-panel-marker"></div>
            <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 16px;">Predicted Logistics Impact</div>
            <div class="supply-cols-row">
                <div class="supply-col-item">
                    <div class="supply-col-label">Corridor Risk</div>
                    <div class="supply-col-val" style="color: #FACC15;">{scenario['risk']}%</div>
                </div>
                <div class="supply-col-item">
                    <div class="supply-col-label">Vehicles Affected</div>
                    <div class="supply-col-val" style="color: #93C5FD;">{scenario['vehicles']}</div>
                </div>
                <div class="supply-col-item">
                    <div class="supply-col-label">Deliveries Affected</div>
                    <div class="supply-col-val" style="color: #C084FC;">{scenario['deliveries']}</div>
                </div>
                <div class="supply-col-item">
                    <div class="supply-col-label">Districts Affected</div>
                    <div class="supply-col-val" style="color: #C084FC;">{scenario['districts']}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        # ------------------------------------------------------------
        # 2. Impact Chain Panel
        # ------------------------------------------------------------
        with st.container(border=True):
            st.markdown(f'''
            <div class="supply-panel-marker"></div>
            <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 16px;">Impact Chain</div>
            <div class="supply-cols-row">
                <div class="supply-col-item">
                    <div class="supply-col-label">⏱️ Estimated Delay</div>
                    <div class="supply-col-val" style="color: #FFFFFF;">+{scenario['delay']} hrs</div>
                </div>
                <div class="supply-col-item">
                    <div class="supply-col-label">⚠️ Supply Risk</div>
                    <div class="supply-col-val" style="color: #FACC15;">{scenario['supply_risk']}%</div>
                </div>
                <div class="supply-col-item">
                    <div class="supply-col-label">🚧 Affected Corridor</div>
                    <div class="supply-col-val" style="color: #93C5FD;">{scenario['corridor']}</div>
                </div>
                <div class="supply-col-item">
                    <div class="supply-col-label">💥 Disruption Level</div>
                    <div class="supply-col-val" style="color: {risk_color};">{risk_level_text}</div>
                </div>
            </div>
            <div style="margin-top: 16px; padding-top: 14px; border-top: 1px solid rgba(32, 196, 255, 0.15); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; font-family: 'Outfit', sans-serif; font-size: 0.85rem; color: rgba(255, 255, 255, 0.85);">
                <div style="display: flex; align-items: center; gap: 6px;"><span>🌧️</span> <span>Environmental Risk</span></div>
                <span style="color: #38BDF8; font-weight: 700;">→</span>
                <div style="display: flex; align-items: center; gap: 6px;"><span>🚧</span> <span>{scenario['corridor']} Inaccessible</span></div>
                <span style="color: #38BDF8; font-weight: 700;">→</span>
                <div style="display: flex; align-items: center; gap: 6px;"><span>🚚</span> <span>{scenario['vehicles']} Vehicles</span></div>
                <span style="color: #38BDF8; font-weight: 700;">→</span>
                <div style="display: flex; align-items: center; gap: 6px;"><span>📦</span> <span>{scenario['deliveries']} Deliveries</span></div>
                <span style="color: #38BDF8; font-weight: 700;">→</span>
                <div style="display: flex; align-items: center; gap: 6px;"><span>🏘️</span> <span>{scenario['districts']} Districts</span></div>
                <span style="color: #38BDF8; font-weight: 700;">→</span>
                <div style="display: flex; align-items: center; gap: 6px;"><span style="color: {risk_color}; font-weight: 700;">Supply Risk: {scenario['supply_risk']}%</span></div>
            </div>
            ''', unsafe_allow_html=True)

        # ------------------------------------------------------------
        # 3. Preventive Recommendation Panel
        # ------------------------------------------------------------
        with st.container(border=True):
            st.markdown(f'''
            <div class="supply-panel-marker"></div>
            <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 16px;">Preventive Recommendation</div>
            <div class="supply-recommendation-content">
                <span style="font-size: 1.1rem; flex-shrink: 0;">🎯</span>
                <span><strong style="color: #38BDF8;">Recommended Action:</strong> {recommendation}</span>
            </div>
            ''', unsafe_allow_html=True)
    
        with st.expander(
            "🔍 How does Impact Before Incident work?"
        ):
    
            st.write(
                """
                The prototype evaluates a potential disruption before
                it becomes a confirmed road closure.
    
                It estimates:
    
                • Corridor risk
                • Potentially affected vehicles
                • Potentially delayed deliveries
                • Affected districts
                • Estimated delivery delay
                • Essential-supply disruption risk
    
                In the production system, these values would be calculated
                using real weather forecasts, GIS road networks, traffic
                data, vehicle GPS, inventory levels, historical incidents
                and machine-learning risk models.
                """
            )
        
    # ============================================================
    # PART 6 — ESSENTIAL CARGO PRIORITY ENGINE
    # ============================================================
    
    # ------------------------------------------------------------
    # Simulated essential cargo data
    # ------------------------------------------------------------
    
    cargo_data = pd.DataFrame([
        {
            "Vehicle": "V03",
            "Cargo": "Medicine",
            "Destination": "Imphal",
            "Supply Remaining": 14,
            "ETA": 8,
            "Road Risk": 82,
            "Population Dependency": "High",
            "Cargo Criticality": "Critical"
        },
        {
            "Vehicle": "V07",
            "Cargo": "Food Supplies",
            "Destination": "Shillong",
            "Supply Remaining": 30,
            "ETA": 5,
            "Road Risk": 21,
            "Population Dependency": "Medium",
            "Cargo Criticality": "High"
        },
        {
            "Vehicle": "V11",
            "Cargo": "Construction Material",
            "Destination": "Aizawl",
            "Supply Remaining": 26,
            "ETA": 7,
            "Road Risk": 38,
            "Population Dependency": "Medium",
            "Cargo Criticality": "Normal"
        },
        {
            "Vehicle": "V15",
            "Cargo": "Medicine",
            "Destination": "Agartala",
            "Supply Remaining": 20,
            "ETA": 6,
            "Road Risk": 25,
            "Population Dependency": "High",
            "Cargo Criticality": "Critical"
        }
    ])
    
    with st.container(border=True):
        st.markdown('''
        <div class="supply-panel-marker"></div>
        <div style="font-family: 'Outfit', sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;">Essential Cargo Priority Engine</div>
        <div style="font-family: 'Outfit', sans-serif; font-size: 0.90rem; color: rgba(255, 255, 255, 0.75); margin-bottom: 16px;">Prototype decision-support engine that prioritizes essential deliveries according to urgency, supply risk and logistics conditions.</div>
        ''', unsafe_allow_html=True)
        
        selected_vehicle = st.selectbox(
            "Select Delivery",
            cargo_data["Vehicle"].tolist()
        )
    
    cargo_row = cargo_data[
        cargo_data["Vehicle"] == selected_vehicle
    ].iloc[0]
    
    # ------------------------------------------------------------
    # Extract values
    # ------------------------------------------------------------
    
    supply_remaining = float(
        cargo_row["Supply Remaining"]
    )
    
    eta = float(
        cargo_row["ETA"]
    )
    
    road_risk = float(
        cargo_row["Road Risk"]
    )
    
    dependency = cargo_row[
        "Population Dependency"
    ]
    
    criticality = cargo_row[
        "Cargo Criticality"
    ]
    
    # ------------------------------------------------------------
    # Convert qualitative factors
    # ------------------------------------------------------------
    
    dependency_score = {
        "Low": 40,
        "Medium": 70,
        "High": 100
    }
    
    criticality_score = {
        "Normal": 40,
        "High": 70,
        "Critical": 100
    }
    
    dependency_value = dependency_score[
        dependency
    ]
    
    criticality_value = criticality_score[
        criticality
    ]
    
    # ------------------------------------------------------------
    # Calculate urgency factors
    # ------------------------------------------------------------
    
    # Lower remaining stock = higher urgency
    stock_urgency = max(
        0,
        100 - (supply_remaining / 48 * 100)
    )
    
    # Higher ETA = higher urgency
    eta_urgency = min(
        (eta / 24) * 100,
        100
    )
    
    # Higher road risk = higher urgency
    road_urgency = road_risk
    
    # ------------------------------------------------------------
    # Priority score
    # ------------------------------------------------------------
    
    priority_score = (
        0.25 * criticality_value
        + 0.20 * dependency_value
        + 0.20 * stock_urgency
        + 0.15 * eta_urgency
        + 0.20 * road_urgency
    )
    
    priority_score = round(
        min(max(priority_score, 0), 100)
    )
    
    # ------------------------------------------------------------
    # 1. Delivery Intelligence Panel
    # ------------------------------------------------------------
    with st.container(border=True):
        st.markdown(f'''
        <div class="supply-panel-marker"></div>
        <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 16px;">Delivery Intelligence</div>
        <div class="supply-cols-row">
            <div class="supply-col-item">
                <div class="supply-col-label">Vehicle</div>
                <div class="supply-col-val" style="color: #93C5FD;">{cargo_row['Vehicle']}</div>
            </div>
            <div class="supply-col-item">
                <div class="supply-col-label">Cargo</div>
                <div class="supply-col-val" style="color: #C084FC;">{cargo_row['Cargo']}</div>
            </div>
            <div class="supply-col-item">
                <div class="supply-col-label">Destination</div>
                <div class="supply-col-val" style="color: #C084FC;">{cargo_row['Destination']}</div>
            </div>
            <div class="supply-col-item">
                <div class="supply-col-label">ETA</div>
                <div class="supply-col-val" style="color: #C084FC;">{eta:.0f} hrs</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    # ------------------------------------------------------------
    # 2. Priority Factors Panel
    # ------------------------------------------------------------
    crit_color = "#FB7185" if criticality == "Critical" else ("#F59E0B" if criticality == "High" else "#10B981")

    with st.container(border=True):
        st.markdown(f'''
        <div class="supply-panel-marker"></div>
        <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 16px;">Priority Factors</div>
        <div class="supply-cols-row">
            <div class="supply-col-item">
                <div class="supply-col-label">📦 Supply Remaining</div>
                <div class="supply-col-val" style="color: #FFFFFF;">{supply_remaining:.0f} hrs</div>
            </div>
            <div class="supply-col-item">
                <div class="supply-col-label">Road Risk</div>
                <div class="supply-col-val" style="color: #FACC15;">{road_risk:.0f}%</div>
            </div>
            <div class="supply-col-item">
                <div class="supply-col-label">Population Dependency</div>
                <div class="supply-col-val" style="color: #C084FC;">{dependency}</div>
            </div>
            <div class="supply-col-item">
                <div class="supply-col-label">Cargo Criticality</div>
                <div class="supply-col-val" style="color: {crit_color};">{criticality}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    # ------------------------------------------------------------
    # 3. AI Priority Assessment Panel
    # ------------------------------------------------------------
    if priority_score >= 75:
        priority_label = "CRITICAL PRIORITY"
        priority_color = "#FB7185"
        priority_desc = "Priority score is high due to low supply, high road risk and critical cargo."
        recommendation = (
            f"Prioritize {cargo_row['Vehicle']} immediately. "
            f"Reroute or protect this {cargo_row['Cargo'].lower()} "
            f"delivery before the current corridor conditions worsen."
        )
    elif priority_score >= 50:
        priority_label = "HIGH PRIORITY"
        priority_color = "#F59E0B"
        priority_desc = "Priority score indicates elevated risk requiring proactive monitoring."
        recommendation = (
            f"Closely monitor {cargo_row['Vehicle']} and prepare "
            f"an alternate route if road conditions deteriorate."
        )
    else:
        priority_label = "NORMAL PRIORITY"
        priority_color = "#10B981"
        priority_desc = "Logistics conditions are within normal operating parameters."
        recommendation = (
            f"Continue normal monitoring of {cargo_row['Vehicle']}."
        )

    with st.container(border=True):
        st.markdown(f'''
        <div class="supply-panel-marker"></div>
        <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 16px;">AI Priority Assessment</div>
        <div class="supply-assessment-split">
            <div class="supply-assessment-left">
                <div class="supply-col-label">Priority Score</div>
                <div class="supply-col-val" style="color: #93C5FD;">{priority_score}/100</div>
            </div>
            <div class="supply-assessment-right">
                <div style="display: flex; align-items: center; gap: 8px; font-family: 'Outfit', sans-serif; font-size: 0.92rem; font-weight: 700; color: {priority_color}; letter-spacing: 0.04em; margin-bottom: 8px;">
                    <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: {priority_color}; box-shadow: 0 0 10px {priority_color};"></span>
                    <span>{priority_label}</span>
                </div>
                <div style="font-family: 'Outfit', sans-serif; font-size: 0.88rem; color: rgba(255, 255, 255, 0.82); line-height: 1.45;">{priority_desc}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    # ------------------------------------------------------------
    # 4. Recommended Action Panel
    # ------------------------------------------------------------
    with st.container(border=True):
        st.markdown(f'''
        <div class="supply-panel-marker"></div>
        <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 16px;">Recommended Action</div>
        <div class="supply-recommendation-content">
            <span style="font-size: 1.1rem; flex-shrink: 0;">🎯</span>
            <span>{recommendation}</span>
        </div>
        ''', unsafe_allow_html=True)
    
    # ------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------
    
    with st.expander(
        "🔍 How is the priority score calculated?"
    ):
    
        st.write(
            f"""
            The prototype combines five factors:
    
            • Cargo criticality: {criticality}
    
            • Population dependency: {dependency}
    
            • Remaining supply: {supply_remaining:.0f} hours
    
            • Vehicle ETA: {eta:.0f} hours
    
            • Road disruption risk: {road_risk:.0f}%
    
            Deliveries carrying more critical goods, serving highly
            dependent populations, having lower remaining stock and
            facing higher logistics risk receive higher priority.
    
            In the production system, these weights would be calibrated
            using historical delivery outcomes, government logistics
            priorities, inventory data, demand forecasts and ML models.
            """
        )
    
    # ------------------------------------------------------------
    # Compare all deliveries
    # ------------------------------------------------------------
    
    with st.container():
        st.markdown('''
        <div class="supply-table-marker"></div>
        <div style="font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin: 20px 0 12px 0;">Delivery Priority Overview</div>
        ''', unsafe_allow_html=True)
        
        priority_table = cargo_data.copy()
        
        def calculate_priority(row):
        
            dependency_value = dependency_score[
                row["Population Dependency"]
            ]
        
            criticality_value = criticality_score[
                row["Cargo Criticality"]
            ]
        
            stock_urgency = max(
                0,
                100 - (row["Supply Remaining"] / 48 * 100)
            )
        
            eta_urgency = min(
                (row["ETA"] / 24) * 100,
                100
            )
        
            road_urgency = row["Road Risk"]
        
            score = (
                0.25 * criticality_value
                + 0.20 * dependency_value
                + 0.20 * stock_urgency
                + 0.15 * eta_urgency
                + 0.20 * road_urgency
            )
        
            return round(
                min(max(score, 0), 100)
            )
        
        priority_table["Priority Score"] = priority_table.apply(
            calculate_priority,
            axis=1
        )
        
        priority_table["Priority"] = priority_table[
            "Priority Score"
        ].apply(
            lambda score:
                "🔴 Critical"
                if score >= 75
                else "🟠 High"
                if score >= 50
                else "🟢 Normal"
        )
        
        priority_table = priority_table.sort_values(
            "Priority Score",
            ascending=False
        )
        
        st.dataframe(
            priority_table[
                [
                    "Vehicle",
                    "Cargo",
                    "Destination",
                    "ETA",
                    "Road Risk",
                    "Priority Score",
                    "Priority"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )
    
    # ============================================================


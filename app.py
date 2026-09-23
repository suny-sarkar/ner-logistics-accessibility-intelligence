import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os

# ---------------------------------------------------------
# IMPORT SUB-MODULES
# ---------------------------------------------------------
from modules.translations import (
    TRANSLATIONS,
    LANGUAGE_OPTIONS,
    localize_number,
    get_language_key,
    get_language_english_name,
)
from modules.navbar import render_top_navbar
from modules.landing import render_landing_page
from modules.overview import render_overview_page
from modules.gis_page import render_gis_page
from modules.weather_page import render_weather_page
from modules.supply_page import render_supply_page
from modules.field_ops_page import render_field_ops_page
from modules.route_optimizer_page import render_route_optimizer_page
from modules.reports_page import render_reports_page
from modules.footer import render_app_footer
from modules.auth_session import (
    get_authenticated_user,
    load_active_session,
    clear_active_session,
    save_active_session,
)

# ---------------------------------------------------------
# PAGE CONFIGURATION (NO SIDEBAR)
# ---------------------------------------------------------
st.set_page_config(
    page_title="NER Logistics Accessibility Intelligence",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# ASSET PRE-LOADER
# ---------------------------------------------------------
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

LANDING_BG_PATH = os.path.join(os.path.dirname(__file__), "assets", "landing_bg.jpg")
MOCKUP_DASH_PATH = os.path.join(os.path.dirname(__file__), "assets", "mockup_dashboard.jpg")

LANDING_BG_B64 = get_base64_image(LANDING_BG_PATH)
MOCKUP_DASHBOARD_B64 = get_base64_image(MOCKUP_DASH_PATH)

# Global full-fledged wallpaper background across the entire platform
st.markdown(f"""
<style>
.stApp {{
    background-color: #070b14 !important;
    background-image: 
        linear-gradient(180deg, rgba(6, 11, 23, 0.20) 0%, rgba(7, 12, 24, 0.48) 100%),
        url('data:image/jpeg;base64,{LANDING_BG_B64}') !important;
    background-size: cover !important;
    background-position: center center !important;
    background-repeat: no-repeat !important;
    background-attachment: fixed !important;
    min-height: 100vh !important;
    color: #e2e8f0 !important;
}}
</style>
""", unsafe_allow_html=True)

# GLOBAL DESIGN SYSTEM & STYLING
# ---------------------------------------------------------
st.markdown("""
<style>
/* Import Modern Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg-primary: #070b14;
    --card-bg: rgba(15, 23, 42, 0.78);
    --card-border: rgba(255, 255, 255, 0.1);
    --accent-cyan: #38bdf8;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* ============================================================
   1. COMPLETELY HIDE SIDEBAR & SIDEBAR CONTROLS
   ============================================================ */
[data-testid="stSidebar"], 
section[data-testid="stSidebar"], 
[data-testid="collapsedControl"], 
div[data-testid="stSidebarNav"] {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    position: absolute !important;
    left: -9999px !important;
}

html, body {
    overflow-x: hidden !important;
    max-width: 100vw !important;
}

/* Full Width Container without Sidebar Margin */
.stApp {{
    background-color: #070b14;
    background-image: 
        radial-gradient(at 0% 0%, rgba(14, 165, 233, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.08) 0px, transparent 50%),
        radial-gradient(at 50% 50%, rgba(15, 23, 42, 0.95) 0px, #070b14 100%);
    background-attachment: fixed;
    color: #e2e8f0;
    overflow-x: hidden !important;
    max-width: 100% !important;
}}

.block-container {{
    padding-top: 1rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 100% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    box-sizing: border-box !important;
}}

@media (max-width: 1024px) {{
    .stApp {{
        background-attachment: scroll !important;
        background-position: center top !important;
    }}
    .block-container {{
        padding-left: 1.25rem !important;
        padding-right: 1.25rem !important;
        padding-top: 0.6rem !important;
    }}
}}

@media (max-width: 640px) {{
    .stApp {{
        background-attachment: scroll !important;
        background-position: center top !important;
    }}
    .block-container {{
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        padding-top: 0.4rem !important;
        padding-bottom: 2rem !important;
    }}
}}

/* ============================================================
   2. TOP STICKY NAVBAR STYLES
   ============================================================ */
.top-navbar-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 10px 22px;
    margin-bottom: 12px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
}

.nav-brand-section {
    display: flex;
    align-items: center;
    gap: 12px;
}

.nav-brand-icon {
    font-size: 1.8rem;
    filter: drop-shadow(0 0 10px rgba(56, 189, 248, 0.6));
}

.nav-brand-title {
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    font-size: 1.15rem;
    letter-spacing: -0.01em;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: block;
}

.nav-brand-sub {
    font-size: 0.72rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
}

.nav-telemetry-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 14px;
    border-radius: 999px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #34d399;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.06em;
}

.nav-pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 10px #10b981;
    display: inline-block;
    animation: pulseGlow 2s infinite;
}

@keyframes pulseGlow {
    0% { transform: scale(0.9); opacity: 0.7; }
    50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 16px #34d399; }
    100% { transform: scale(0.9); opacity: 0.7; }
}

.nav-right-section {
    display: flex;
    align-items: center;
    gap: 12px;
}

/* ============================================================
   SINGLE UNIFIED DARK-BLUE NAVBAR CONTAINER ADJUSTMENTS
   ============================================================ */
div[data-testid="element-container"]:has(.ner-navbar-wrapper) {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}


/* ============================================================
   3. LANDING PAGE (SCREEN 1) STYLES
   ============================================================ */
.landing-full-hero {
    position: relative;
    border-radius: 24px;
    background-size: cover;
    background-position: center 36%;
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.85);
    padding: 38px 32px;
    margin-bottom: 2rem;
    overflow: hidden;
}

.landing-left-container {
    padding-right: 14px;
}

.landing-brand-badge {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 20px;
}

.landing-brand-title {
    font-family: 'Outfit', sans-serif;
    font-size: 2.2rem;
    font-weight: 900;
    color: #ffffff;
    margin: 0;
    line-height: 1.1;
    text-shadow: 0 2px 14px rgba(0,0,0,0.8);
}

.landing-brand-sub {
    font-size: 1.05rem;
    color: #38bdf8;
    font-weight: 700;
    margin: 2px 0 0 0;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.landing-hook-box {
    margin-bottom: 20px;
}

.landing-hook-main {
    font-family: 'Outfit', sans-serif;
    font-size: 1.75rem;
    font-weight: 800;
    line-height: 1.25;
    color: #ffffff;
    margin-bottom: 8px;
    text-shadow: 0 2px 14px rgba(0, 0, 0, 0.8);
    background: linear-gradient(135deg, #ffffff 40%, #bae6fd 80%, #7dd3fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.landing-hook-desc {
    font-size: 0.95rem;
    color: #cbd5e1;
    line-height: 1.5;
    margin-bottom: 16px;
    text-shadow: 0 1px 4px rgba(0,0,0,0.6);
}

.landing-map-wrapper {
    position: relative;
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid rgba(56, 189, 248, 0.3);
    box-shadow: 0 12px 30px -8px rgba(0, 0, 0, 0.7);
    background: rgba(15, 23, 42, 0.6);
}

.landing-map-img {
    width: 100%;
    height: auto;
    display: block;
    border-radius: 16px;
    filter: saturate(1.15) contrast(1.1);
}

.landing-map-caption {
    background: rgba(15, 23, 42, 0.85);
    padding: 8px 12px;
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 600;
    text-align: center;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
}

/* Floating Login Modal (Center) */
.landing-login-modal {
    background: rgba(15, 23, 42, 0.82);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 20px;
    padding: 24px 22px 12px 22px;
    box-shadow: 0 20px 45px -10px rgba(0, 0, 0, 0.8);
}

.landing-login-header {
    text-align: center;
}

/* Vertical Feature Pills (Right) */
.landing-features-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.landing-feature-pill {
    background: rgba(15, 23, 42, 0.65);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: all 0.25s ease;
    box-shadow: 0 6px 16px -4px rgba(0,0,0,0.4);
}

.landing-feature-pill:hover {
    transform: translateX(4px);
    background: rgba(30, 41, 59, 0.8);
    border-color: rgba(56, 189, 248, 0.4);
}

.landing-feature-icon {
    font-size: 1.4rem;
    filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.4));
}

.landing-feature-text {
    flex: 1;
}

.landing-feature-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #f8fafc;
}

.landing-feature-sub {
    font-size: 0.72rem;
    color: #94a3b8;
}

/* ============================================================
   4. OVERVIEW COMMAND CENTER (SCREEN 2) STYLES
   ============================================================ */
.overview-header-ribbon {
    background: rgba(15, 23, 42, 0.75);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 14px 22px;
    margin-bottom: 16px;
}

.overview-map-card {
    position: relative;
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid rgba(56, 189, 248, 0.3);
    box-shadow: 0 14px 35px -10px rgba(0, 0, 0, 0.7);
    margin-bottom: 12px;
}

.overview-map-img {
    width: 100%;
    height: auto;
    display: block;
    filter: saturate(1.15) contrast(1.1);
}

.overview-map-overlay-badge {
    position: absolute;
    bottom: 10px;
    left: 14px;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #38bdf8;
}

.telemetry-weather-card {
    background: rgba(15, 23, 42, 0.75);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 12px;
}

.telemetry-kpi-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 12px;
}

.telemetry-kpi-chip {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.kpi-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 8px;
}

.kpi-dot.green { background: #10b981; box-shadow: 0 0 8px #10b981; }
.kpi-dot.red { background: #ef4444; box-shadow: 0 0 8px #ef4444; }
.kpi-dot.amber { background: #f97316; box-shadow: 0 0 8px #f97316; }
.kpi-dot.yellow { background: #eab308; box-shadow: 0 0 8px #eab308; }
.kpi-dot.pink { background: #ec4899; box-shadow: 0 0 8px #ec4899; }

.kpi-label {
    font-size: 0.8rem;
    color: #cbd5e1;
    font-weight: 600;
    flex: 1;
}

.kpi-val {
    font-size: 1.15rem;
    font-weight: 800;
    color: #ffffff;
    font-family: 'Outfit', sans-serif;
}

.telemetry-alert-card {
    background: rgba(30, 20, 25, 0.75);
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-radius: 16px;
    padding: 14px 16px;
}

.overview-footer-banner {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 12px 20px;
    text-align: center;
    margin-top: 18px;
    font-size: 0.95rem;
}

/* Streamlit Button & Widget Polish */
.stButton>button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px -4px rgba(0, 0, 0, 0.5);
}

.stTextInput>div>div>input {
    background-color: rgba(15, 23, 42, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 10px !important;
    color: #f8fafc !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# AUTHENTICATION, SESSION PERSISTENCE & QUERY PARAMETER ROUTER
# ---------------------------------------------------------
qp = st.query_params

if qp.get("action") == "logout":
    clear_active_session()
    st.session_state.authenticated = False
    st.session_state.current_page = "overview"
    st.query_params.clear()
    st.rerun()

# Single Source of Truth for Logged-In User
auth_user = get_authenticated_user()

if auth_user:
    st.session_state.authenticated = True
    st.session_state.authenticated_user = auth_user
    st.session_state.user_name = auth_user.get("name", "Field Officer")
    st.session_state.user_role = auth_user.get("role", "Field Officer")
    st.session_state.access_profile = auth_user.get("access_profile", auth_user.get("role", "Field Officer"))
    st.session_state.officer_id = auth_user.get("user_id", "NER-OFC-001")
    st.session_state.department = auth_user.get("department", "Assam Highway Command & BRO")
    st.session_state.organization = auth_user.get("organization", "NorthEast Express Logistics")
else:
    st.session_state.authenticated = False
    st.session_state.authenticated_user = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "overview"

if "selected_language" not in st.session_state:
    st.session_state.selected_language = "en"

if "lang" in qp:
    target_lang = qp.get("lang")
    st.session_state.selected_language = get_language_key(target_lang)

is_transporter = (st.session_state.get("user_role") == "Commercial Transporter")

if "nav" in qp:
    target_nav = qp.get("nav", "home").lower()
    if is_transporter and target_nav not in ["home", "overview"]:
        st.session_state.current_page = "overview"
        st.query_params["nav"] = "home"
    else:
        if target_nav in ["home", "overview"]:
            st.session_state.current_page = "overview"
        elif target_nav in ["gis", "vehicle_location", "road_accessibility", "gis_fleet"]:
            st.session_state.current_page = "gis"
        elif target_nav in ["weather", "weather_conditions", "weather_ai"]:
            st.session_state.current_page = "weather"
        elif target_nav in ["supply", "supply_requirements", "cargo_priority", "supply_cargo"]:
            st.session_state.current_page = "supply"
        elif target_nav in ["field_ops", "infrastructure_incidents"]:
            st.session_state.current_page = "field_ops"
        elif target_nav in ["route_optimizer", "route_conditions", "ai_router"]:
            st.session_state.current_page = "route_optimizer"
        elif target_nav in ["reports", "field_reports"]:
            st.session_state.current_page = "reports"
        else:
            st.session_state.current_page = target_nav

# Multilingual Translations handler
current_lang_code = get_language_key(st.session_state.get("selected_language", "en"))
current_language_key = get_language_english_name(current_lang_code)
T = TRANSLATIONS.get(current_lang_code, TRANSLATIONS.get(current_language_key, TRANSLATIONS["en"]))

# ---------------------------------------------------------
# MULTI-PAGE APPLICATION ROUTER
# ---------------------------------------------------------

if not st.session_state.authenticated:
    # SCREEN 1: Dedicated Pre-Login Landing Page
    render_landing_page(LANDING_BG_B64)

else:
    # POST-LOGIN: Top Sticky Navbar + Active Sub-Page
    if is_transporter:
        st.session_state.current_page = "overview"
        if st.query_params.get("nav", "").lower() not in ["home", "overview", ""]:
            st.query_params["nav"] = "home"

    render_top_navbar()

    page = st.session_state.current_page

    if page == "overview":
        # SCREEN 2: Command Center Dashboard
        render_overview_page(MOCKUP_DASHBOARD_B64, T, current_language_key, localize_number)

    elif page in ["gis", "vehicle_location", "road_accessibility"]:
        render_gis_page()

    elif page in ["weather", "weather_conditions"]:
        render_weather_page()

    elif page in ["supply", "supply_requirements", "cargo_priority"]:
        render_supply_page()

    elif page in ["field_ops", "infrastructure_incidents"]:
        render_field_ops_page()

    elif page in ["route_optimizer", "route_conditions"]:
        render_route_optimizer_page()

    elif page in ["reports", "field_reports"]:
        render_reports_page()

    else:
        render_overview_page(MOCKUP_DASHBOARD_B64, T, current_language_key, localize_number)

    # Render Shared Enterprise Application Footer
    render_app_footer()

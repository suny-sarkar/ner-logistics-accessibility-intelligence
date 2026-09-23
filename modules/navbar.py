import streamlit as st
import textwrap
import os
import json
import html
from modules.auth_session import get_authenticated_user
from modules.translations import (
    NAVBAR_TRANSLATIONS,
    LANGUAGE_OPTIONS,
    SUPPORTED_LANGUAGES,
    get_language_key,
    get_language_display_name,
)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
_SYNCED_REPORTS_FILE = os.path.join(_DATA_DIR, "synchronized_reports.json")
_PENDING_REPORTS_FILE = os.path.join(_DATA_DIR, "pending_offline_reports.json")

def _get_latest_field_ops_reports(limit=5):
    """
    Retrieves the newest Field Ops incident reports up to `limit` (max 5).
    Reads directly from persistent storage files and current session state.
    Returns reports ordered from newest to oldest.
    """
    raw_reports = []
    seen_ids = set()

    for filepath in [_SYNCED_REPORTS_FILE, _PENDING_REPORTS_FILE]:
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                rid = item.get("report_id")
                                if rid and rid not in seen_ids:
                                    seen_ids.add(rid)
                                    raw_reports.append(item)
                                elif not rid:
                                    raw_reports.append(item)
            except Exception:
                pass

    if "fo_last_submission" in st.session_state and isinstance(st.session_state.fo_last_submission, dict):
        last_sub = st.session_state.fo_last_submission
        rid = last_sub.get("report_id")
        if rid and rid not in seen_ids:
            seen_ids.add(rid)
            raw_reports.append(last_sub)
        elif not rid and last_sub not in raw_reports:
            raw_reports.append(last_sub)

    if "offline_reports" in st.session_state and isinstance(st.session_state.offline_reports, list):
        for item in st.session_state.offline_reports:
            if isinstance(item, dict):
                rid = item.get("report_id")
                if rid and rid not in seen_ids:
                    seen_ids.add(rid)
                    raw_reports.append(item)

    if "submitted_reports" in st.session_state and isinstance(st.session_state.submitted_reports, list):
        for item in st.session_state.submitted_reports:
            if isinstance(item, dict):
                rid = item.get("report_id")
                if rid and rid not in seen_ids:
                    seen_ids.add(rid)
                    raw_reports.append(item)

    def get_sort_key(r):
        return str(r.get("timestamp") or r.get("created_at") or r.get("synced_at") or "")

    raw_reports.sort(key=get_sort_key, reverse=True)
    return raw_reports[:limit]

def _format_ticker_item(report, idx=1):
    inc_type = report.get("incident_type", "Incident")
    if inc_type in ["Other", "Others"] and report.get("other_incident"):
        inc_type = report.get("other_incident")

    district = report.get("district", "")
    corridor = report.get("corridor", "")
    loc = report.get("location") or ""
    if not loc:
        parts = [p for p in [district, corridor] if p]
        loc = ", ".join(parts) if parts else "NER Corridor"

    severity = str(report.get("severity", "ALERT")).upper()
    status_raw = str(report.get("status", "Active"))
    if "Pending" in status_raw:
        status_label = "PENDING"
        status_class = "ticker-status-pending"
    else:
        status_label = "SYNCED"
        status_class = "ticker-status-synced"

    if severity == "CRITICAL":
        sev_icon = "🚨"
        sev_class = "ticker-sev-critical"
    elif severity == "HIGH":
        sev_icon = "⚠️"
        sev_class = "ticker-sev-high"
    elif severity in ["MEDIUM", "MODERATE"]:
        sev_icon = "⚡"
        sev_class = "ticker-sev-medium"
    else:
        sev_icon = "ℹ️"
        sev_class = "ticker-sev-low"

    rep_id = report.get("report_id", "")
    id_html = f'<span class="ticker-id">({html.escape(rep_id)})</span>' if rep_id else ""

    return (
        f'<span class="nav-ticker-item">'
        f'<span class="ticker-seq-badge">{idx}</span>'
        f'<span class="ticker-icon">{sev_icon}</span>'
        f'<span class="ticker-severity-badge {sev_class}">{html.escape(severity)}</span>'
        f'<span class="ticker-type">{html.escape(inc_type)}</span>'
        f'<span class="ticker-sep">·</span>'
        f'<span class="ticker-loc">📍 {html.escape(loc)}</span>'
        f'<span class="ticker-sep">·</span>'
        f'<span class="ticker-status-badge {status_class}">{status_label}</span>'
        f'{id_html}'
        f'</span>'
    )

def _build_ticker_html(reports):
    if reports:
        items_html = "".join(_format_ticker_item(r, idx=i + 1) for i, r in enumerate(reports))
        if len(reports) == 1:
            cycle_html = items_html * 4
        elif len(reports) == 2:
            cycle_html = items_html * 2
        elif len(reports) == 3:
            cycle_html = items_html * 2
        else:
            cycle_html = items_html
    else:
        fallback_item = (
            '<span class="nav-ticker-item">'
            '<span class="ticker-seq-badge">1</span>'
            '<span class="ticker-icon">🚨</span>'
            '<span class="ticker-severity-badge ticker-sev-high">FIELD OPS</span>'
            '<span class="ticker-type">Standby Monitoring</span>'
            '<span class="ticker-sep">·</span>'
            '<span class="ticker-loc">📍 All NER Corridors Monitored</span>'
            '<span class="ticker-sep">·</span>'
            '<span class="ticker-status-badge ticker-status-synced">ACTIVE</span>'
            '</span>'
        )
        cycle_html = fallback_item * 3

    return (
        f'<div class="nav-ticker-panel" aria-label="Incident Alert Ticker" role="region">'
        f'<div class="nav-ticker-label-box">'
        f'<span class="nav-ticker-dot"></span>'
        f'<span>ALERTS</span>'
        f'</div>'
        f'<div class="nav-ticker-viewport">'
        f'<div class="nav-ticker-track">'
        f'<div class="nav-ticker-content">{cycle_html}</div>'
        f'<div class="nav-ticker-content" aria-hidden="true">{cycle_html}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )

def h(html_str):
    """
    Strips leading and trailing whitespace from every line so that
    Streamlit's markdown renderer never interprets lines as indented code blocks.
    """
    return "\n".join(line.strip() for line in html_str.splitlines() if line.strip())

def render_top_navbar(languages=None, on_language_change=None):
    """
    Renders the unified top header and navigation bar of the NER Logistics
    Accessibility Intelligence platform matching all refined requirements:

    1. Structure:
       - Header row:
         * Left: Brand title ("NER LOGISTICS INTELLIGENCE") + subtitle
         * Center: Live telemetry status pill ("LIVE TELEMETRY: 8 NE STATES ACTIVE") with pulsing green dot
         * Right: Inspector badge + Outlined danger Logout pill + Pure-CSS mobile hamburger button
       - Navigation bar:
         * Strict order: Home -> GIS Fleet -> Weather AI -> Supply & Cargo -> Field Ops -> AI Router
         * Followed by pure-CSS language selector dropdown
       - Rendered as styled HTML via st.markdown(navbar_html, unsafe_allow_html=True)

    2. Styling:
       - All nav items share deep-blue background (no individual light/white card backgrounds)
       - Screens >900px: evenly spaced across full width (justify-content: space-between), single line, no wrapping
       - 2px accent cyan animated underline on hover, persistent on active item
       - Responsive breakpoints:
         * >1200px: full desktop layout
         * 900-1200px: same layout, slightly reduced padding/font size
         * 640-900px: compact left-aligned single row with scroll/overflow, wrapped header if needed
         * <640px: telemetry pill hidden, hamburger visible; checkbox :checked expands stacked vertical list
       - Zero JavaScript for toggling or language switching (pure HTML links & CSS)
    """
    # Read language from query params first, fallback to session state, default to 'en'
    qp_lang = st.query_params.get("lang", "")
    if qp_lang:
        st.session_state.selected_language = get_language_key(qp_lang)
    elif "selected_language" not in st.session_state:
        st.session_state.selected_language = "en"

    active_lang_key = get_language_key(st.session_state.get("selected_language", "en"))
    active_display_lang = get_language_display_name(active_lang_key)

    auth_user = st.session_state.get("authenticated_user") or get_authenticated_user()
    if auth_user:
        user_role = auth_user.get("role", "Field Officer")
        user_name = auth_user.get("name", "Field Officer")
        officer_id = auth_user.get("user_id", "NER-OFC-001")
    else:
        user_role = st.session_state.get("user_role", "Field Officer")
        user_name = st.session_state.get("user_name", "Inspector R. K. Sharma")
        officer_id = st.session_state.get("officer_id", "NER-OFC-001")

    # Read active page from query params first, fallback to session state
    qp_nav = st.query_params.get("nav", "").lower()
    current_page = qp_nav if qp_nav else st.session_state.get("current_page", "overview").lower()
    if user_role == "Commercial Transporter":
        current_page = "overview"

    # Badge styling
    if user_role == "Field Officer":
        user_badge_text = f"👮 {user_name} ({officer_id})"
        badge_style = "background: rgba(2, 132, 199, 0.18); border: 1px solid rgba(56, 189, 248, 0.45); color: #7dd3fc;"
    elif user_role == "Commercial Transporter":
        user_badge_text = f"👤 {user_name} [Commercial Transporter]"
        badge_style = "background: rgba(16, 185, 129, 0.18); border: 1px solid rgba(52, 211, 153, 0.45); color: #6ee7b7;"
    else:
        user_badge_text = f"👤 {user_name} [General]"
        badge_style = "background: rgba(16, 185, 129, 0.18); border: 1px solid rgba(52, 211, 153, 0.45); color: #6ee7b7;"

    # Active page classification
    is_home = current_page in ["overview", "home", ""]
    is_gis = current_page in ["gis", "vehicle_location", "road_accessibility", "gis_fleet"]
    is_weather = current_page in ["weather", "weather_conditions", "weather_ai"]
    is_supply = current_page in ["supply", "supply_requirements", "cargo_priority", "supply_cargo"]
    is_ops = current_page in ["field_ops", "infrastructure_incidents"]
    is_router = current_page in ["route_optimizer", "route_conditions", "ai_router"]

    active_home = "active" if is_home else ""
    active_gis = "active" if is_gis else ""
    active_weather = "active" if is_weather else ""
    active_supply = "active" if is_supply else ""
    active_ops = "active" if is_ops else ""
    active_router = "active" if is_router else ""

    current_nav_slug = "home" if is_home else ("gis" if is_gis else ("weather" if is_weather else ("supply" if is_supply else ("field_ops" if is_ops else "route_optimizer"))))

    # Build pure HTML/CSS language dropdown links (No JS onchange handler)
    lang_links_html = ""
    for item in SUPPORTED_LANGUAGES:
        code = item["code"]
        display_name = item["display"]
        is_active = (code == active_lang_key)
        active_class = "active" if is_active else ""
        lang_links_html += f'<a href="?nav={current_nav_slug}&lang={code}" class="nav-lang-item {active_class}" target="_self">{display_name}</a>\n'

    # Retrieve centralized navbar display translations for active language
    t_nav = NAVBAR_TRANSLATIONS.get(active_lang_key, NAVBAR_TRANSLATIONS["en"])

    # Build Center Header Element (Incident Alert Ticker on Home; Live Telemetry on other pages)
    if is_home:
        latest_reports = _get_latest_field_ops_reports(limit=5)
        center_header_html = _build_ticker_html(latest_reports)
    else:
        center_header_html = """
        <div class="nav-telemetry-pill" aria-live="polite">
          <span class="nav-pulse-dot" aria-hidden="true"></span>
          <span class="nav-telemetry-text">LIVE TELEMETRY: 8 NE STATES ACTIVE</span>
        </div>
        """

    navbar_html = f"""
    <style>
    /* ============================================================
       0. STREAMLIT CONTAINER OVERRIDES (FULL-WIDTH TOP NAVBAR IN NORMAL FLOW)
       ============================================================ */
    header[data-testid="stHeader"],
    .stAppHeader {{
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }}

    [data-testid="stMain"],
    .stMain {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}

    /* Override Streamlit's centered content constraint: 100% width, 0 top/side padding */
    .stApp:has(.ner-navbar-wrapper) .stMainBlockContainer,
    .stApp:has(.ner-navbar-wrapper) .block-container,
    .stMainBlockContainer:has(.ner-navbar-wrapper),
    .block-container:has(.ner-navbar-wrapper) {{
        width: 100% !important;
        max-width: 100% !important;
        padding-top: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        margin-top: 0 !important;
        box-sizing: border-box !important;
    }}

    /* Move navbar element container to the absolute first visual position with zero spacing */
    div[data-testid="element-container"]:has(.ner-navbar-wrapper),
    div[data-testid="stElementContainer"]:has(.ner-navbar-wrapper),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.ner-navbar-wrapper) {{
        order: -9999 !important;
        width: 100% !important;
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }}

    /* Hide style-only element containers in stVerticalBlock so they take 0 space and generate no flex gaps */
    div[data-testid="stElementContainer"]:has(> div[data-testid="stMarkdown"] > div > div:only-child > style:only-child),
    div[data-testid="element-container"]:has(> div[data-testid="stMarkdown"] > div > div:only-child > style:only-child),
    div[data-testid="stElementContainer"]:has(style:only-child):not(:has(.ner-navbar-wrapper)),
    div[data-testid="element-container"]:has(style:only-child):not(:has(.ner-navbar-wrapper)) {{
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    /* Ensure vertical block has zero top offset */
    .stApp:has(.ner-navbar-wrapper) div[data-testid="stVerticalBlock"],
    .stMainBlockContainer:has(.ner-navbar-wrapper) > div[data-testid="stVerticalBlock"],
    .block-container:has(.ner-navbar-wrapper) > div[data-testid="stVerticalBlock"] {{
        margin-top: 0 !important;
        padding-top: 0 !important;
    }}

    /* Re-apply comfortable side padding to all page content below the navbar (excluding full-width footer) */
    .stApp:has(.ner-navbar-wrapper) div[data-testid="stMainBlockContainer"] > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)),
    .stApp:has(.ner-navbar-wrapper) .block-container > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)),
    .stMainBlockContainer:has(.ner-navbar-wrapper) > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)),
    .block-container:has(.ner-navbar-wrapper) > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)),
    .stApp:has(.ner-navbar-wrapper) .block-container > div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)) {{
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        box-sizing: border-box !important;
    }}

    /* ============================================================
       1. NER LOGISTICS UNIFIED FULL-WIDTH TOP NAVBAR
       ============================================================ */
    .ner-navbar-wrapper {{
        width: 100% !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 32px !important;
        position: relative;
        z-index: 100;
        box-sizing: border-box !important;
        overflow: visible !important;
    }}

    .ner-navbar {{
        background: linear-gradient(180deg, #0d1630 0%, #0a1024 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-top: none !important;
        border-left: none !important;
        border-right: none !important;
        border-bottom: 1px solid rgba(56, 189, 248, 0.25) !important;
        border-radius: 0 !important;
        padding: 16px 2rem 14px 2rem;
        box-shadow: 0 10px 30px -4px rgba(0, 0, 0, 0.65), 0 0 20px rgba(14, 165, 233, 0.08);
        position: relative;
        width: 100% !important;
        box-sizing: border-box !important;
        min-height: 100px;
        overflow: visible !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}

    /* Hidden Checkbox for pure CSS mobile menu toggle */
    .nav-toggle-checkbox {{
        display: none !important;
    }}

    /* ------------------------------------------------------------
       1. TOP HEADER ROW (Brand + Status + Inspector + Logout + Hamburger)
       ------------------------------------------------------------ */
    .nav-header-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .nav-brand-block {{
        display: flex;
        flex-direction: column;
        flex-shrink: 0;
    }}

    .nav-brand-title {{
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 800;
        font-size: 1.25rem;
        line-height: 1.35;
        letter-spacing: -0.01em;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-decoration: none;
        display: inline-block;
        padding-top: 4px;
        padding-bottom: 2px;
        transition: opacity 0.2s ease;
    }}

    .nav-brand-title:hover {{
        opacity: 0.88;
    }}

    .nav-brand-sub {{
        font-size: 0.72rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
        margin-top: 2px;
    }}

    /* Center Live Telemetry Pill */
    .nav-telemetry-pill {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 5px 14px;
        border-radius: 999px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #34d399;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        white-space: nowrap;
    }}

    .nav-pulse-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 10px #10b981;
        display: inline-block;
        animation: navPulseGlow 2s infinite;
    }}

    @keyframes navPulseGlow {{
        0% {{ transform: scale(0.9); opacity: 0.7; }}
        50% {{ transform: scale(1.25); opacity: 1; box-shadow: 0 0 14px #34d399; }}
        100% {{ transform: scale(0.9); opacity: 0.7; }}
    }}

    /* ============================================================
       INCIDENT-ALERT TICKER (HOME NAVBAR)
       ============================================================ */
    .nav-ticker-panel {{
        display: inline-flex;
        align-items: center;
        background: #020617;
        border: 1px solid rgba(239, 68, 68, 0.55);
        border-radius: 999px;
        height: 32px;
        max-width: 560px;
        min-width: 220px;
        flex: 1 1 auto;
        margin: 0 14px;
        overflow: hidden;
        position: relative;
        box-shadow: 0 0 14px rgba(220, 38, 38, 0.22), inset 0 1px 3px rgba(0, 0, 0, 0.9);
        box-sizing: border-box;
    }}

    .nav-ticker-label-box {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(220, 38, 38, 0.22);
        border-right: 1px solid rgba(239, 68, 68, 0.35);
        padding: 0 10px;
        height: 100%;
        color: #f87171;
        font-size: 0.70rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        flex-shrink: 0;
        z-index: 2;
        white-space: nowrap;
    }}

    .nav-ticker-dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #ef4444;
        box-shadow: 0 0 8px #ef4444;
        animation: navAlertPulse 1.8s infinite;
    }}

    @keyframes navAlertPulse {{
        0%, 100% {{ transform: scale(0.9); opacity: 0.7; }}
        50% {{ transform: scale(1.25); opacity: 1; box-shadow: 0 0 12px #ff4d4f; }}
    }}

    .nav-ticker-viewport {{
        flex: 1 1 auto;
        overflow: hidden;
        position: relative;
        height: 100%;
        display: flex;
        align-items: center;
        mask-image: linear-gradient(90deg, transparent 0px, #000 12px, #000 calc(100% - 12px), transparent 100%);
        -webkit-mask-image: linear-gradient(90deg, transparent 0px, #000 12px, #000 calc(100% - 12px), transparent 100%);
    }}

    .nav-ticker-track {{
        display: inline-flex;
        align-items: center;
        white-space: nowrap;
        width: max-content;
        animation: tickerScrollLeftToRight 28s linear infinite;
        will-change: transform;
    }}

    .nav-ticker-track:hover {{
        animation-play-state: paused;
    }}

    @keyframes tickerScrollLeftToRight {{
        0% {{
            transform: translateX(-50%);
        }}
        100% {{
            transform: translateX(0%);
        }}
    }}

    .nav-ticker-content {{
        display: inline-flex;
        align-items: center;
        white-space: nowrap;
    }}

    .nav-ticker-item {{
        display: inline-flex;
        align-items: center;
        gap: 7px;
        margin-right: 48px;
        font-size: 0.76rem;
        font-weight: 600;
        color: #f87171;
        letter-spacing: 0.02em;
        white-space: nowrap;
    }}

    .ticker-seq-badge {{
        background: rgba(239, 68, 68, 0.35);
        border: 1px solid rgba(239, 68, 68, 0.7);
        color: #ffffff;
        font-weight: 800;
        font-size: 0.70rem;
        padding: 1px 7px;
        border-radius: 999px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-right: 2px;
        box-shadow: 0 0 6px rgba(239, 68, 68, 0.4);
        flex-shrink: 0;
        letter-spacing: 0;
    }}

    .ticker-icon {{
        font-size: 0.82rem;
        flex-shrink: 0;
    }}

    .ticker-severity-badge {{
        font-size: 0.68rem;
        font-weight: 800;
        padding: 1px 6px;
        border-radius: 4px;
        letter-spacing: 0.04em;
        flex-shrink: 0;
    }}

    .ticker-sev-critical {{
        background: rgba(239, 68, 68, 0.25);
        border: 1px solid rgba(239, 68, 68, 0.6);
        color: #fca5a5;
    }}

    .ticker-sev-high {{
        background: rgba(249, 115, 22, 0.25);
        border: 1px solid rgba(249, 115, 22, 0.6);
        color: #fdba74;
    }}

    .ticker-sev-medium {{
        background: rgba(245, 158, 11, 0.22);
        border: 1px solid rgba(245, 158, 11, 0.5);
        color: #fde047;
    }}

    .ticker-sev-low {{
        background: rgba(56, 189, 248, 0.2);
        border: 1px solid rgba(56, 189, 248, 0.45);
        color: #7dd3fc;
    }}

    .ticker-type {{
        color: #ffffff;
        font-weight: 700;
    }}

    .ticker-sep {{
        color: rgba(239, 68, 68, 0.45);
        font-weight: 700;
    }}

    .ticker-loc {{
        color: #fca5a5;
        font-weight: 600;
    }}

    .ticker-status-badge {{
        font-size: 0.64rem;
        font-weight: 700;
        padding: 1px 5px;
        border-radius: 4px;
        flex-shrink: 0;
    }}

    .ticker-status-synced {{
        background: rgba(16, 185, 129, 0.18);
        border: 1px solid rgba(52, 211, 153, 0.45);
        color: #6ee7b7;
    }}

    .ticker-status-pending {{
        background: rgba(245, 158, 11, 0.18);
        border: 1px solid rgba(245, 158, 11, 0.45);
        color: #fcd34d;
    }}

    .ticker-id {{
        color: #94a3b8;
        font-size: 0.68rem;
        font-weight: 500;
    }}

    /* Right Header Actions: Officer Badge + Outlined Danger Logout + Mobile Hamburger */
    .nav-header-actions {{
        display: flex;
        align-items: center;
        gap: 12px;
        flex-shrink: 0;
    }}

    .nav-officer-pill,
    .nav-officer-pill * {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        border-radius: 999px;
        padding: 5px 14px;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 0.76rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em !important;
        line-height: 1.2 !important;
        text-rendering: optimizeLegibility !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
        white-space: nowrap;
        vertical-align: middle !important;
        box-sizing: border-box;
    }}

    /* Red Danger Action Logout Pill: Red background with white text */
    .nav-logout-pill {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 999px;
        padding: 5px 16px;
        font-size: 0.80rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-decoration: none !important;
        text-transform: uppercase;
        color: #ffffff !important;
        background: #dc2626;
        border: 1px solid #ef4444;
        cursor: pointer;
        transition: all 250ms ease;
        white-space: nowrap;
        box-shadow: 0 2px 8px rgba(220, 38, 38, 0.35);
    }}

    .nav-logout-pill:hover {{
        background: #b91c1c;
        border-color: #f87171;
        color: #ffffff !important;
        box-shadow: 0 0 14px rgba(239, 68, 68, 0.65);
        transform: translateY(-1px);
    }}

    .nav-logout-pill:focus-visible {{
        outline: 2px solid #ef4444;
        outline-offset: 2px;
    }}

    /* Hamburger Toggle Button (Hidden on desktop/tablet, visible on <640px) */
    .nav-hamburger-btn {{
        display: none;
        flex-direction: column;
        justify-content: space-between;
        width: 24px;
        height: 18px;
        cursor: pointer;
        padding: 0;
        margin-left: 6px;
    }}

    .nav-hamburger-btn .bar {{
        height: 2px;
        width: 100%;
        background: #38bdf8;
        border-radius: 2px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    /* ------------------------------------------------------------
       2. NAVIGATION BAR (Second Row: Home -> GIS Fleet -> Weather AI ...)
       ------------------------------------------------------------ */
    .nav-items-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        padding-top: 6px;
        width: 100%;
    }}

    /* Nav Links Group: Flex space-between on desktop */
    .nav-links-group {{
        flex: 1;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        flex-wrap: nowrap;
    }}

    /* Clean text-only navigation links (NO background/box, underline ONLY on hover & active) */
    .nav-link {{
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: transparent !important;
        background-color: transparent !important;
        color: #94a3b8;
        font-size: 1.02rem;
        font-weight: 600;
        letter-spacing: 0.01em;
        text-decoration: none !important;
        padding: 8px 4px;
        margin: 0;
        white-space: nowrap;
        cursor: pointer;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        outline: none;
        transition: color 200ms ease;
    }}

    .nav-link:hover {{
        color: #ffffff;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        text-decoration: none !important;
        transform: none !important;
    }}

    /* 2px accent cyan animated underline on hover */
    .nav-link::after {{
        content: '';
        position: absolute;
        bottom: 0px;
        left: 0;
        width: 100%;
        height: 2px;
        background: #38bdf8;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.85);
        border-radius: 2px;
        transform: scaleX(0);
        transform-origin: center;
        opacity: 0;
        transition: transform 250ms cubic-bezier(0.16, 1, 0.3, 1), opacity 250ms ease;
        pointer-events: none;
    }}

    .nav-link:hover::after {{
        transform: scaleX(1);
        opacity: 1;
    }}

    /* Active navigation item: text color + persistent cyan underline (NO box background) */
    .nav-link.active {{
        color: #38bdf8;
        font-weight: 700;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        text-decoration: none !important;
    }}

    .nav-link.active::after {{
        transform: scaleX(1);
        opacity: 1;
        background: #38bdf8;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.9);
    }}

    .nav-link:focus-visible {{
        outline: 2px solid #38bdf8;
        outline-offset: 3px;
    }}

    /* Pure-CSS Language Selector Dropdown (No JS onchange needed) */
    .nav-lang-container {{
        flex-shrink: 0;
        margin-left: 14px;
        position: relative;
    }}

    .nav-lang-dropdown {{
        position: relative;
        display: inline-block;
    }}

    .nav-lang-btn {{
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 8px;
        color: #ffffff !important;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 5px 12px;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: all 250ms ease;
        outline: none;
        white-space: nowrap;
    }}

    .nav-lang-current {{
        color: #ffffff !important;
        font-weight: 700;
    }}

    .nav-lang-dropdown:hover .nav-lang-btn,
    .nav-lang-dropdown:focus-within .nav-lang-btn {{
        color: #ffffff !important;
        border-color: #38bdf8;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.35);
    }}

    .nav-lang-caret {{
        font-size: 0.65rem;
        color: #ffffff !important;
        transition: transform 0.2s ease;
    }}

    .nav-lang-dropdown:hover .nav-lang-caret,
    .nav-lang-dropdown:focus-within .nav-lang-caret {{
        transform: rotate(180deg);
    }}

    .nav-lang-menu {{
        display: none;
        position: absolute;
        right: 0;
        top: 100%;
        margin-top: 6px;
        background: rgba(10, 16, 36, 0.98);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 10px;
        min-width: 155px;
        box-shadow: 0 12px 28px -4px rgba(0, 0, 0, 0.7), 0 0 16px rgba(14, 165, 233, 0.15);
        z-index: 999;
        padding: 6px 0;
    }}

    .nav-lang-dropdown:hover .nav-lang-menu,
    .nav-lang-dropdown:focus-within .nav-lang-menu {{
        display: flex;
        flex-direction: column;
        animation: navDropdownFade 0.2s ease forwards;
    }}

    .nav-lang-item {{
        display: block;
        padding: 8px 14px;
        color: #ffffff !important;
        font-size: 0.82rem;
        text-decoration: none;
        font-weight: 600;
        transition: all 150ms ease;
        white-space: nowrap;
    }}

    .nav-lang-item:hover {{
        background: rgba(56, 189, 248, 0.18);
        color: #ffffff !important;
        padding-left: 18px;
    }}

    .nav-lang-item.active {{
        color: #ffffff !important;
        background: rgba(56, 189, 248, 0.28);
        font-weight: 700;
    }}

    @keyframes navDropdownFade {{
        from {{ opacity: 0; transform: translateY(-4px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* ------------------------------------------------------------
       3. RESPONSIVE BREAKPOINTS
       ------------------------------------------------------------ */

    /* Desktop (>1200px): evenly spread full-width in one line */
    @media (min-width: 1201px) {{
        .nav-links-group {{
            justify-content: space-between;
        }}
    }}

    /* Laptop / Small Desktop (900-1200px): evenly-spaced single line, comfortable readable font */
    @media (min-width: 901px) and (max-width: 1200px) {{
        .ner-navbar {{
            padding: 12px 18px 10px 18px !important;
        }}
        .nav-link {{
            font-size: 0.94rem;
            padding: 6px 2px;
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}
        .nav-brand-title {{
            font-size: 1.15rem;
            line-height: 1.35;
        }}
        .nav-telemetry-pill {{
            font-size: 0.74rem;
            padding: 4px 10px;
        }}
        .nav-ticker-panel {{
            max-width: 400px !important;
            margin: 0 10px !important;
        }}
        .nav-ticker-item {{
            margin-right: 36px !important;
            font-size: 0.73rem !important;
        }}
        .nav-officer-pill {{
            font-size: 0.76rem;
            padding: 4px 10px;
        }}
        .nav-logout-pill {{
            font-size: 0.76rem;
            padding: 5px 12px;
        }}
    }}

    /* Tablet (641-1024px): edge-to-edge navbar, comfortable spacing */
    @media (min-width: 641px) and (max-width: 1024px) {{
        .ner-navbar-wrapper {{
            width: 100% !important;
            max-width: 100% !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            margin-top: 0 !important;
            margin-bottom: 32px !important;
        }}
        .ner-navbar {{
            padding: 12px 1.25rem 10px 1.25rem !important;
            border-radius: 0 !important;
        }}
        .stApp:has(.ner-navbar-wrapper) div[data-testid="stMainBlockContainer"] > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)),
        .stApp:has(.ner-navbar-wrapper) .block-container > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)),
        .stMainBlockContainer:has(.ner-navbar-wrapper) > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)),
        .block-container:has(.ner-navbar-wrapper) > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)) {{
            padding-left: 1.25rem !important;
            padding-right: 1.25rem !important;
        }}
        .nav-header-row {{
            flex-wrap: wrap;
            gap: 10px;
        }}
        .nav-telemetry-pill {{
            font-size: 0.72rem;
            padding: 4px 8px;
        }}
        .nav-ticker-panel {{
            max-width: 340px !important;
            margin: 0 8px !important;
        }}
        .nav-ticker-item {{
            margin-right: 28px !important;
            font-size: 0.70rem !important;
        }}
        .nav-officer-pill {{
            font-size: 0.74rem;
            padding: 4px 8px;
        }}
        .nav-logout-pill {{
            font-size: 0.74rem;
            padding: 5px 10px;
        }}
        .nav-links-group {{
            justify-content: flex-start;
            gap: 16px;
            overflow-x: auto;
        }}
        .nav-link {{
            font-size: 0.90rem;
            padding: 6px 4px;
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}
    }}

    /* Mobile (<640px): Brand + Logout + Hamburger, edge-to-edge with clean gap */
    @media (max-width: 640px) {{
        .ner-navbar-wrapper {{
            width: 100% !important;
            max-width: 100% !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            margin-top: 0 !important;
            margin-bottom: 32px !important;
        }}
        .ner-navbar {{
            padding: 12px 0.75rem 10px 0.75rem !important;
            border-radius: 0 !important;
        }}
        .stApp:has(.ner-navbar-wrapper) div[data-testid="stMainBlockContainer"] > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)),
        .stApp:has(.ner-navbar-wrapper) .block-container > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)),
        .stMainBlockContainer:has(.ner-navbar-wrapper) > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)),
        .block-container:has(.ner-navbar-wrapper) > div[data-testid="stVerticalBlock"] > div:not(:has(.ner-navbar-wrapper)):not(:has(.app-footer-wrapper)) {{
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }}
        .nav-header-row {{
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            gap: 8px !important;
            width: 100% !important;
            box-sizing: border-box !important;
            padding-bottom: 0px;
            border-bottom: none;
        }}
        .nav-brand-block {{
            flex: 1 1 auto !important;
            min-width: 0 !important;
            overflow: hidden !important;
        }}
        .nav-brand-title {{
            font-size: 1.05rem;
            line-height: 1.25;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .nav-brand-sub {{
            font-size: 0.66rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        /* Hide LIVE TELEMETRY pill and ticker panel on mobile to reduce clutter */
        .nav-telemetry-pill,
        .nav-ticker-panel {{
            display: none !important;
        }}
        .nav-officer-pill {{
            display: none !important;
        }}
        .nav-header-actions {{
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            gap: 8px !important;
            flex-shrink: 0 !important;
            margin-left: auto !important;
        }}
        .nav-logout-pill {{
            font-size: 0.72rem;
            padding: 4px 10px;
            flex-shrink: 0 !important;
        }}
        /* Show Hamburger toggle button inside the header actions row */
        .nav-hamburger-btn {{
            display: flex !important;
            flex-shrink: 0 !important;
            margin-left: 2px !important;
        }}
        /* Hide nav-items row by default on mobile */
        .nav-items-row {{
            display: none;
            flex-direction: column;
            align-items: stretch;
            gap: 6px;
            padding-top: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            margin-top: 10px;
        }}
        /* Pure CSS Checkbox Toggle: expand menu when checked */
        .nav-toggle-checkbox:checked ~ .nav-items-row {{
            display: flex !important;
            animation: navSlideDown 0.25s ease forwards;
        }}
        .nav-links-group {{
            flex-direction: column;
            align-items: stretch;
            gap: 4px;
            width: 100%;
        }}
        .nav-link {{
            justify-content: flex-start;
            padding: 10px 0;
            font-size: 1.0rem;
            border: none !important;
            border-radius: 0 !important;
            background: transparent !important;
            background-color: transparent !important;
            box-shadow: none !important;
            width: 100%;
            text-decoration: none !important;
        }}
        .nav-link:hover,
        .nav-link:focus-visible {{
            color: #ffffff;
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            text-decoration: none !important;
        }}
        .nav-link.active {{
            color: #38bdf8;
            font-weight: 700;
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            text-decoration: none !important;
        }}
        .nav-link::after {{
            bottom: 0px;
            left: 0;
            width: 100%;
            height: 2px;
            background: #38bdf8;
        }}
        .nav-link:hover::after,
        .nav-link.active::after {{
            transform: scaleX(1);
            opacity: 1;
        }}
        /* Full-width language dropdown below stacked links on mobile */
        .nav-lang-container {{
            margin-left: 0;
            margin-top: 8px;
            width: 100%;
        }}
        .nav-lang-dropdown {{
            width: 100%;
        }}
        .nav-lang-btn {{
            width: 100%;
            justify-content: space-between;
            padding: 9px 12px;
            font-size: 0.88rem;
        }}
        .nav-lang-menu {{
            position: static;
            width: 100%;
            margin-top: 4px;
            box-shadow: none;
            border: 1px solid rgba(56, 189, 248, 0.2);
        }}
        /* Hamburger animation to 'X' */
        .nav-toggle-checkbox:checked ~ .nav-header-row .bar-1 {{
            transform: translateY(8px) rotate(45deg);
        }}
        .nav-toggle-checkbox:checked ~ .nav-header-row .bar-2 {{
            opacity: 0;
        }}
        .nav-toggle-checkbox:checked ~ .nav-header-row .bar-3 {{
            transform: translateY(-8px) rotate(-45deg);
        }}
    }}

    @keyframes navSlideDown {{
        from {{
            opacity: 0;
            transform: translateY(-8px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    </style>

    <div class="ner-navbar-wrapper">
      <header class="ner-navbar" role="banner">
        <!-- Hidden Checkbox for Pure-CSS Mobile Hamburger Toggle -->
        <input type="checkbox" id="nav-toggle" class="nav-toggle-checkbox" aria-label="Toggle navigation menu">

        <!-- 1. Header Row (Brand + Status + Inspector + Logout + Hamburger) -->
        <div class="nav-header-row">
          <!-- Left: Brand Block -->
          <div class="nav-brand-block">
            <a href="?nav=home" class="nav-brand-title" target="_self" title="NER Logistics Intelligence">
              NER LOGISTICS INTELLIGENCE
            </a>
            <div class="nav-brand-sub">
              Accessibility Intelligence Platform · Northeast Mission
            </div>
          </div>

          <!-- Center: Live Telemetry Status Pill (Other Pages) OR Incident Alert Ticker (Home Page) -->
          {center_header_html}

          <!-- Right: Inspector Info + Outlined Danger Logout Pill + Mobile Hamburger -->
          <div class="nav-header-actions">
            <div class="nav-officer-pill" style="{badge_style}">
              {user_badge_text}
            </div>

            <a href="?action=logout" class="nav-logout-pill" target="_self" role="button" title="Sign out of session">
              Logout
            </a>

            <label for="nav-toggle" class="nav-hamburger-btn" aria-label="Toggle navigation menu" role="button" tabindex="0">
              <span class="bar bar-1"></span>
              <span class="bar bar-2"></span>
              <span class="bar bar-3"></span>
            </label>
          </div>
        </div>

        <!-- 2. Navigation Bar (Second Row: Home -> GIS Fleet -> Weather AI -> Supply & Cargo -> Field Ops -> AI Router) -->
        <nav class="nav-items-row" id="navbar-menu" role="navigation" aria-label="Main Navigation">
          <!-- Links Group: Evenly distributed with flex space-between -->
          <div class="nav-links-group">
            <a href="?nav=home&lang={active_lang_key}" class="nav-link {active_home}" target="_self">{t_nav['home']}</a>
            <a href="?nav=gis&lang={active_lang_key}" class="nav-link {active_gis}" target="_self">{t_nav['gis']}</a>
            <a href="?nav=weather&lang={active_lang_key}" class="nav-link {active_weather}" target="_self">{t_nav['weather']}</a>
            <a href="?nav=supply&lang={active_lang_key}" class="nav-link {active_supply}" target="_self">{t_nav['supply']}</a>
            <a href="?nav=field_ops&lang={active_lang_key}" class="nav-link {active_ops}" target="_self">{t_nav['field_ops']}</a>
            <a href="?nav=route_optimizer&lang={active_lang_key}" class="nav-link {active_router}" target="_self">{t_nav['route_optimizer']}</a>
          </div>

          <!-- Language Selector Dropdown (Pure HTML/CSS Links, No JavaScript) -->
          <div class="nav-lang-container">
            <div class="nav-lang-dropdown">
              <div class="nav-lang-btn" tabindex="0" role="button" aria-haspopup="true">
                <span>🌐</span>
                <span class="nav-lang-current">{active_display_lang}</span>
                <span class="nav-lang-caret">▾</span>
              </div>
              <div class="nav-lang-menu">
                {lang_links_html}
              </div>
            </div>
          </div>
        </nav>
      </header>
    </div>
    """

    st.markdown(h(navbar_html), unsafe_allow_html=True)

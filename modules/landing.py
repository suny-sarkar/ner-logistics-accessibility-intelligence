import streamlit as st
import streamlit.components.v1 as components
import base64
import os
from modules.typography import animated_heading, animated_text, animated_paragraph
from modules.auth_session import save_active_session

def clean_html(html_str):
    """
    Strips leading and trailing whitespace from each line to completely prevent
    markdown parsers from accidentally creating monospace code blocks.
    """
    return "".join(line.strip() for line in html_str.splitlines())

# ---------------------------------------------------------
# LOGIN MODAL DIALOG (Streamlit 1.34+ native @st.dialog)
# ---------------------------------------------------------
@st.dialog("Sign In to Operations Console", width="small")
def render_login_modal():
    st.markdown(clean_html("""
    <div style="text-align: center; margin-bottom: 12px;">
        <div style="font-family:'Outfit',sans-serif; font-size: 1.4rem; font-weight: 800; color: #0f172a; margin-top: 4px;">
            NER Logistics Portal
        </div>
        <div style="font-size: 0.78rem; color: #0284c7; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">
            Accessibility Intelligence Command
        </div>
    </div>
    """), unsafe_allow_html=True)

    login_tab1, login_tab2 = st.tabs([
        "Sign In", 
        "Create Account"
    ])

    # TAB 1: Standard Credentials
    with login_tab1:
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        role_choice = st.radio(
            "Access Profile:",
            ["Field Officer", "Commercial Transporter"],
            key="modal_role_select",
            horizontal=True
        )
        is_officer = ("Field Officer" in role_choice)

        with st.form(key="modal_signin_form"):
            default_user = "admin.officer@ner.gov.in" if is_officer else "transporter@ne-express.in"
            email_val = st.text_input("Email or Service Badge ID", value=default_user, key="modal_email")
            pass_val = st.text_input("Password", type="password", value="ner2026secure", key="modal_pass")
            
            c_rem, c_forgot = st.columns([1, 1])
            with c_rem:
                st.checkbox("Remember me", value=True, key="modal_remember")
            with c_forgot:
                st.markdown("<div style='text-align:right; font-size:0.75rem; padding-top:6px;'><a href='#' style='color:#38bdf8;'>Forgot password?</a></div>", unsafe_allow_html=True)

            btn_submit = st.form_submit_button("Enter Operations Console", type="primary", use_container_width=True)
            if btn_submit:
                clean_val = email_val.strip() if email_val else ""
                extracted_id = None
                if "(" in clean_val and ")" in clean_val:
                    parts = clean_val.split("(")
                    clean_val = parts[0].strip()
                    extracted_id = parts[1].replace(")", "").strip()

                if is_officer:
                    role_str = "Field Officer"
                    if clean_val and clean_val != "admin.officer@ner.gov.in":
                        if "@" in clean_val:
                            u_name = clean_val.split("@")[0].replace(".", " ").title()
                        else:
                            u_name = clean_val
                    else:
                        u_name = "Inspector R. K. Sharma"
                    u_id = extracted_id or "NER-OFC-001"
                    dept = "Assam Highway Command & BRO"
                    org = "NorthEast Express Logistics"
                else:
                    role_str = "Commercial Transporter"
                    if clean_val and clean_val != "transporter@ne-express.in":
                        if "@" in clean_val:
                            u_name = clean_val.split("@")[0].replace(".", " ").title()
                        else:
                            u_name = clean_val
                    else:
                        u_name = "Tashi Namgyal"
                    u_id = extracted_id or "NER-TRP-042"
                    dept = ""
                    org = "NorthEast Express Logistics"

                user_payload = {
                    "name": u_name,
                    "role": role_str,
                    "access_profile": role_str,
                    "user_id": u_id,
                    "email": clean_val if "@" in clean_val else (f"{u_name.lower().replace(' ', '.')}@ner.gov.in" if is_officer else f"{u_name.lower().replace(' ', '.')}@transporter.in"),
                    "department": dept,
                    "organization": org,
                    "authenticated": True
                }
                save_active_session(user_payload)
                st.session_state.current_page = "overview"
                st.query_params["nav"] = "home"
                st.rerun()

    # TAB 2: Register Account
    with login_tab2:

        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        with st.form(key="modal_reg_form"):
            su_role = st.radio("Register As:", ["Field Officer Profile", "Commercial Fleet Transporter"], key="modal_su_role", horizontal=True)
            su_name = st.text_input("Full Name", placeholder="e.g. Captain Ananya Gogoi", key="modal_su_name")
            su_id = st.text_input("Badge ID / Fleet Company", placeholder="e.g. BRO-8842-AS or Barak Cargo Lines", key="modal_su_id")
            su_pass = st.text_input("Password", type="password", placeholder="Enter Password", key="modal_su_pass")
            
            su_btn = st.form_submit_button("Register & Enter Console", type="primary", use_container_width=True)
            if su_btn:
                if su_name.strip():
                    is_su_officer = ("Field Officer" in su_role)
                    role_str = "Field Officer" if is_su_officer else "Commercial Transporter"
                    u_name = su_name.strip()
                    u_id = su_id.strip() if su_id.strip() else ("NER-OFC-001" if is_su_officer else "NER-TRP-088")
                    user_payload = {
                        "name": u_name,
                        "role": role_str,
                        "access_profile": role_str,
                        "user_id": u_id,
                        "email": f"{u_name.lower().replace(' ', '.')}@ner.gov.in" if is_su_officer else f"{u_name.lower().replace(' ', '.')}@transporter.in",
                        "department": "Assam Highway Command & BRO" if is_su_officer else "",
                        "organization": su_id.strip() if (su_id.strip() and not is_su_officer) else "NorthEast Express Logistics",
                        "authenticated": True
                    }
                    save_active_session(user_payload)
                    st.session_state.current_page = "overview"
                    st.query_params["nav"] = "home"
                    st.rerun()
                else:
                    st.error("Please enter your name.")


# ---------------------------------------------------------
# PROFESSIONAL LANDING PAGE
# ---------------------------------------------------------
def render_landing_page(bg_b64):
    """
    Renders a high-impact, professional enterprise landing page:
    - Full-cover continuous mountain highway wallpaper background
    - Elegant top glassmorphic navbar with brand, live telemetry badge, and 'Sign In' CTA
    - Hero section with bold typography, platform mission, and 'Launch Console' actions
    - Live Strategic Corridors preview
    - 4 Core Architectural Capabilities cards with custom background imagery
    - Embedded Jitter Motion Architecture Reel
    """
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
    def get_card_b64(fname):
        fp = os.path.join(assets_dir, fname)
        if os.path.exists(fp):
            with open(fp, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return ""

    card_gis_b64 = get_card_b64("card_gis_radar.png")
    card_hazard_b64 = get_card_b64("card_hazard_ai.png")
    card_supply_b64 = get_card_b64("card_supply.png")
    card_command_b64 = get_card_b64("card_command.png")

    # Global CSS for the Professional Landing Page
    st.markdown(clean_html(f"""
    <style>
    /* Full-bleed background image with crystal-clear full-fledged vibrancy */
    .stApp {{
        background-color: #050811 !important;
        background-image: 
            linear-gradient(180deg, rgba(5, 9, 20, 0.14) 0%, rgba(6, 11, 23, 0.42) 100%),
            url('data:image/jpeg;base64,{bg_b64}') !important;
        background-size: cover !important;
        background-position: center 25% !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
        min-height: 100vh !important;
        width: 100% !important;
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }}

    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 4rem !important;
        max-width: 1350px !important;
        margin: 0 auto !important;
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
            padding-top: 0.75rem !important;
            padding-bottom: 3rem !important;
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
            padding-top: 0.5rem !important;
            padding-bottom: 2rem !important;
        }}
    }}

    /* Top Glass Navbar - High Translucency */
    .landing-top-bar {{
        background: rgba(13, 21, 38, 0.52);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        padding: 14px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: clamp(1.8rem, 4vw, 3.5rem);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }}

    .landing-brand {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .landing-brand-icon {{
        font-size: clamp(1.4rem, 3vw, 1.8rem);
        filter: drop-shadow(0 0 12px rgba(56, 189, 248, 0.6));
    }}
    .landing-brand-title {{
        font-family: 'Outfit', sans-serif;
        font-size: clamp(1.02rem, 2.4vw, 1.25rem) !important;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.01em;
        line-height: 1.2;
    }}
    .landing-brand-title span {{
        color: #38bdf8;
    }}
    .landing-brand-sub {{
        font-size: clamp(0.62rem, 1.3vw, 0.72rem) !important;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }}

    .nav-live-wrapper {{
        padding-top: 6px;
        text-align: right;
    }}
    .nav-live-pill {{
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(52, 211, 153, 0.4);
        color: #6ee7b7;
        font-size: clamp(0.68rem, 1.3vw, 0.75rem) !important;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 999px;
        display: inline-flex;
        align-items: center;
        gap: 7px;
        white-space: nowrap;
    }}
    .pulse-dot-live {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 8px #10b981;
        display: inline-block;
    }}

    @media (max-width: 640px) {{
        .landing-brand {{
            gap: 8px;
        }}
        .landing-brand-sub {{
            display: none !important;
        }}
        .nav-live-wrapper {{
            padding-top: 4px;
            text-align: center;
        }}
        .nav-live-pill {{
            padding: 3px 8px !important;
            font-size: 0.64rem !important;
            gap: 5px;
        }}
    }}

    /* Hero Section */
    .hero-container {{
        text-align: center;
        max-width: 960px;
        margin: 0 auto clamp(1.6rem, 4vw, 3rem) auto;
        padding: 0 8px;
        box-sizing: border-box;
    }}
    .hero-badge {{
        display: inline-block;
        background: rgba(56, 189, 248, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.35);
        color: #38bdf8;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        padding: 6px 18px;
        border-radius: 999px;
        margin-bottom: 1.2rem;
    }}
    /* Modern Animated Fluid Hero Typography */
    @keyframes heroEntrance {{
        0% {{
            opacity: 0;
            transform: translateY(24px);
            filter: blur(8px);
        }}
        100% {{
            opacity: 1;
            transform: translateY(0);
            filter: blur(0);
        }}
    }}

    @keyframes metallicShimmer {{
        0% {{ background-position: 0% center; }}
        100% {{ background-position: 200% center; }}
    }}

    @keyframes auroraFlow {{
        0% {{
            background-position: 0% 50%;
        }}
        50% {{
            background-position: 100% 50%;
        }}
        100% {{
            background-position: 0% 50%;
        }}
    }}

    @keyframes floatGentle {{
        0%, 100% {{
            transform: translateY(0);
        }}
        50% {{
            transform: translateY(-6px);
        }}
    }}

    .hero-title {{
        font-family: 'Outfit', sans-serif;
        font-size: clamp(1.85rem, 4.8vw, 3.35rem) !important;
        font-weight: 900;
        line-height: clamp(1.16, 1.2, 1.25) !important;
        letter-spacing: -0.025em;
        margin-bottom: clamp(0.8rem, 2vw, 1.3rem) !important;
        position: relative;
        word-wrap: break-word;
    }}

    /* Cinematic Typography System Styles */
    .split-word {{
        display: inline-block !important;
        white-space: nowrap !important;
        vertical-align: baseline !important;
    }}
    .split-char {{
        display: inline-block !important;
        will-change: transform, opacity, filter !important;
        backface-visibility: hidden !important;
        -webkit-backface-visibility: hidden !important;
    }}
    /* Ensure metallic text continues through split characters cleanly */
    .hero-title-prefix .split-word,
    .hero-title-prefix .split-char {{
        display: inline-block !important;
        background: inherit !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }}

    /* Compact, Small Hero CTA Button */
    div.st-key-hero_access_btn {{
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        max-width: 250px !important;
        margin: 0 auto !important;
    }}
    div.st-key-hero_access_btn > div,
    div.st-key-hero_access_btn [data-testid="stButton"] {{
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }}
    div.st-key-hero_access_btn button,
    div.st-key-hero_access_btn [data-testid="baseButton-primary"] {{
        width: auto !important;
        max-width: 240px !important;
        min-width: 195px !important;
        padding: clamp(7px, 1.6vw, 9px) clamp(16px, 2.5vw, 20px) !important;
        font-size: clamp(0.82rem, 1.8vw, 0.88rem) !important;
        font-weight: 700 !important;
        letter-spacing: 0.015em !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 14px rgba(239, 68, 68, 0.32) !important;
        white-space: nowrap !important;
        display: inline-flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0 auto !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    div.st-key-hero_access_btn button:hover,
    div.st-key-hero_access_btn [data-testid="baseButton-primary"]:hover {{
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(239, 68, 68, 0.48) !important;
    }}

    /* Top Corner Sign In / Log In Button - Short, Sleek & Compact for Desktop */
    div.st-key-top_nav_signin_btn {{
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
        width: 100% !important;
    }}
    div.st-key-top_nav_signin_btn > div,
    div.st-key-top_nav_signin_btn [data-testid="stButton"] {{
        display: flex !important;
        justify-content: flex-end !important;
        width: auto !important;
    }}
    div.st-key-top_nav_signin_btn button,
    div.st-key-top_nav_signin_btn [data-testid="baseButton-primary"] {{
        white-space: nowrap !important;
        width: auto !important;
        min-width: 115px !important;
        max-width: 142px !important;
        margin-left: auto !important;
        padding: 7px 15px !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        border-radius: 9px !important;
        letter-spacing: 0.02em !important;
        box-shadow: 0 2px 10px rgba(239, 68, 68, 0.25) !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    div.st-key-top_nav_signin_btn button:hover,
    div.st-key-top_nav_signin_btn [data-testid="baseButton-primary"]:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.45) !important;
    }}

    @media (max-width: 640px) {{
        div.st-key-top_nav_signin_btn button,
        div.st-key-top_nav_signin_btn [data-testid="baseButton-primary"] {{
            min-width: 96px !important;
            max-width: 120px !important;
            padding: 5px 10px !important;
            font-size: 0.74rem !important;
        }}
    }}

    /* Section Typography Styles */
    .section-title {{
        font-family: 'Outfit', sans-serif !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        margin: 0 0 6px 0 !important;
    }}
    h2.section-title {{
        font-size: clamp(1.25rem, 2.8vw, 1.65rem) !important;
    }}
    h3.section-title {{
        font-size: clamp(1.02rem, 2.2vw, 1.18rem) !important;
    }}
    .section-desc {{
        color: #94a3b8 !important;
        font-size: clamp(0.78rem, 1.6vw, 0.88rem) !important;
        margin: 0 !important;
        line-height: 1.5 !important;
    }}

    .hero-title-prefix {{
        display: inline-block;
        background: linear-gradient(110deg, #ffffff 30%, #94a3b8 50%, #ffffff 70%);
        background-size: 200% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: metallicShimmer 6s ease-in-out infinite;
        text-shadow: 0 4px 20px rgba(0, 0, 0, 0.8);
    }}

    .hero-title-highlight {{
        display: inline-block;
        margin-top: 6px;
        background: linear-gradient(
            135deg, 
            #38bdf8 0%, 
            #818cf8 25%, 
            #34d399 50%, 
            #38bdf8 75%, 
            #60a5fa 100%
        );
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: auroraFlow 4.5s ease-in-out infinite, floatGentle 5s ease-in-out infinite;
        position: relative;
        cursor: default;
        transition: transform 0.3s ease;
    }}

    .hero-title-highlight:hover {{
        transform: scale(1.02);
    }}

    /* Remove any pseudo-elements or anchor links near headings */
    .hero-title-highlight::after,
    .hero-title-highlight::before {{
        display: none !important;
        content: none !important;
    }}

    a.anchor-link,
    .anchorjs-link,
    [data-testid="stMarkdownContainer"] h1 a,
    [data-testid="stMarkdownContainer"] h2 a,
    [data-testid="stMarkdownContainer"] h3 a {{
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }}
    .hero-desc {{
        font-size: clamp(0.88rem, 1.7vw, 1.12rem) !important;
        color: #cbd5e1;
        line-height: clamp(1.48, 1.6, 1.65) !important;
        max-width: 780px;
        margin: 0 auto clamp(1.2rem, 3vw, 2rem) auto;
        font-weight: 400;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.8);
        padding: 0 8px;
    }}

    /* Strategic Corridors Live Telemetry Responsive Grid */
    .corridor-container {{
        background: rgba(13, 21, 38, 0.75);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 16px;
        padding: clamp(14px, 2.5vw, 20px) clamp(16px, 3vw, 24px);
        margin-bottom: clamp(2rem, 4vw, 3.5rem);
    }}
    .corridor-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
        flex-wrap: wrap;
        gap: 10px;
    }}
    .corridor-sub {{
        font-size: clamp(0.68rem, 1.4vw, 0.75rem);
        color: #94a3b8;
    }}
    .corridor-telemetry-status {{
        font-size: clamp(0.68rem, 1.4vw, 0.75rem);
        font-family: 'JetBrains Mono', monospace;
        color: #38bdf8;
    }}
    .corridor-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
    }}
    .corridor-card {{
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        padding: clamp(10px, 1.8vw, 12px);
        box-sizing: border-box;
    }}
    .corridor-title {{
        font-size: clamp(0.68rem, 1.3vw, 0.74rem);
        font-weight: 700;
    }}
    .corridor-status {{
        font-size: clamp(0.85rem, 1.8vw, 0.95rem);
        font-weight: 800;
        color: #fff;
        margin-top: 2px;
    }}
    .corridor-detail {{
        font-size: clamp(0.66rem, 1.2vw, 0.72rem);
        color: #94a3b8;
        margin-top: 4px;
        line-height: 1.4;
    }}

    @media (max-width: 1024px) {{
        .corridor-grid {{
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 12px !important;
        }}
    }}
    @media (max-width: 600px) {{
        .corridor-grid {{
            grid-template-columns: 1fr !important;
            gap: 10px !important;
        }}
        .corridor-container {{
            padding: 14px 14px !important;
            margin-bottom: 2rem !important;
        }}
    }}

    /* Floating Stats Bar - Translucent Frosted Glass */
    .stats-bar-grid {{
        background: rgba(13, 21, 38, 0.55);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 18px;
        padding: 20px 28px;
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin-bottom: 3.5rem;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
    }}
    @media (max-width: 1024px) {{
        .stats-bar-grid {{
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            padding: 16px 20px;
            margin-bottom: 2.5rem;
        }}
    }}
    @media (max-width: 600px) {{
        .stats-bar-grid {{
            grid-template-columns: 1fr;
            gap: 12px;
            padding: 14px 16px;
            margin-bottom: 2rem;
        }}
        .stat-item {{
            border-right: none !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.10);
            padding-bottom: 10px;
        }}
        .stat-item:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}
    }}
    .stat-item {{
        text-align: center;
        border-right: 1px solid rgba(255, 255, 255, 0.10);
    }}
    .stat-item:last-child {{
        border-right: none;
    }}
    .stat-number {{
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem;
        font-weight: 900;
        color: #38bdf8;
        line-height: 1;
        margin-bottom: 4px;
        text-shadow: 0 0 20px rgba(56, 189, 248, 0.5);
    }}
    .stat-label {{
        font-size: 0.82rem;
        color: #f1f5f9;
        font-weight: 600;
    }}
    .stat-sub {{
        font-size: 0.72rem;
        color: #cbd5e1;
        margin-top: 2px;
    }}

    /* 4 Feature Pillar Cards - Premium Jitter Cinematic Animation System */
    .features-grid {{
        display: grid !important;
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 24px !important;
        margin-bottom: 3.5rem !important;
        width: 100% !important;
        box-sizing: border-box !important;
        position: relative;
    }}

    /* Card Container Base Styling */
    .feature-card {{
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 18px;
        padding: 24px 20px;
        min-height: 295px;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        box-shadow: 0 14px 35px rgba(0, 0, 0, 0.55);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-sizing: border-box;
        transform: translate3d(0, 35px, 0) scale(0.94);
        opacity: 0;
        filter: blur(6px);
        transition: transform 0.45s cubic-bezier(0.16, 1, 0.3, 1),
                    border-color 0.4s ease-out,
                    box-shadow 0.45s cubic-bezier(0.16, 1, 0.3, 1);
        will-change: transform, opacity, filter;
    }}

    /* Separate Background Layer (receives parallax only, text isolated) */
    .feature-card-bg {{
        position: absolute;
        top: -16px;
        left: -16px;
        right: -16px;
        bottom: -16px;
        z-index: 1;
        border-radius: 22px;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        pointer-events: none;
        transform: translate3d(0, 0, 0) scale(1.08);
        opacity: 0.75;
        filter: blur(2px) brightness(0.85);
        transition: transform 0.45s cubic-bezier(0.16, 1, 0.3, 1),
                    filter 0.45s ease-out,
                    opacity 0.45s ease-out;
        will-change: transform;
    }}

    /* Card background images and dark gradient overlays */
    .feature-card-gis .feature-card-bg {{
        background: linear-gradient(180deg, rgba(8, 14, 28, 0.38) 0%, rgba(7, 12, 24, 0.85) 55%, rgba(5, 9, 18, 0.98) 100%),
                    url('data:image/png;base64,{card_gis_b64}') center/cover no-repeat !important;
    }}
    .feature-card-hazard .feature-card-bg {{
        background: linear-gradient(180deg, rgba(8, 14, 28, 0.38) 0%, rgba(7, 12, 24, 0.85) 55%, rgba(5, 9, 18, 0.98) 100%),
                    url('data:image/png;base64,{card_hazard_b64}') center/cover no-repeat !important;
    }}
    .feature-card-supply .feature-card-bg {{
        background: linear-gradient(180deg, rgba(8, 14, 28, 0.38) 0%, rgba(7, 12, 24, 0.85) 55%, rgba(5, 9, 18, 0.98) 100%),
                    url('data:image/png;base64,{card_supply_b64}') center/cover no-repeat !important;
    }}
    .feature-card-command .feature-card-bg {{
        background: linear-gradient(180deg, rgba(8, 14, 28, 0.38) 0%, rgba(7, 12, 24, 0.85) 55%, rgba(5, 9, 18, 0.98) 100%),
                    url('data:image/png;base64,{card_command_b64}') center/cover no-repeat !important;
    }}

    /* Separate Content Layer (no parallax translation, pure stability) */
    .feature-card-content {{
        position: relative;
        z-index: 2;
        width: 100%;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        pointer-events: none;
        box-sizing: border-box;
    }}

    .feature-icon-box {{
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(56, 189, 248, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.95rem;
        font-weight: 800;
        color: #38bdf8;
        font-family: 'Outfit', sans-serif;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        opacity: 0;
        transform: translate3d(0, -8px, 0) scale(0.8);
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
        will-change: transform, opacity;
    }}
    .feature-heading {{
        font-family: 'Outfit', sans-serif;
        font-size: 1.22rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 6px;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.8);
        line-height: 1.25;
        word-wrap: break-word;
        opacity: 0;
        transform: translate3d(0, 12px, 0);
        will-change: transform, opacity;
    }}
    .feature-desc {{
        font-size: 0.84rem;
        color: #e2e8f0;
        line-height: 1.5;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.9);
        margin: 0;
        word-wrap: break-word;
        opacity: 0;
        transform: translate3d(0, 12px, 0);
        will-change: transform, opacity;
    }}

    /* ============================================================
       JITTER CINEMATIC ENTRANCE KEYFRAMES
       ============================================================ */
    @keyframes jitterCardEntrance {{
        0% {{
            opacity: 0;
            transform: translate3d(0, 35px, 0) scale(0.94);
            filter: blur(6px);
        }}
        100% {{
            opacity: 1;
            transform: translate3d(0, 0, 0) scale(1);
            filter: blur(0px);
        }}
    }}

    @keyframes jitterImageEntrance {{
        0% {{
            opacity: 0.75;
            transform: translate3d(0, 0, 0) scale(1.08);
            filter: blur(2px) brightness(0.85);
        }}
        100% {{
            opacity: 1;
            transform: translate3d(0, 0, 0) scale(1);
            filter: blur(0px) brightness(1);
        }}
    }}

    @keyframes jitterBadgeEntrance {{
        0% {{
            opacity: 0;
            transform: translate3d(0, -8px, 0) scale(0.8);
        }}
        100% {{
            opacity: 1;
            transform: translate3d(0, 0, 0) scale(1);
        }}
    }}

    @keyframes jitterHeadingEntrance {{
        0% {{
            opacity: 0;
            transform: translate3d(0, 12px, 0);
        }}
        100% {{
            opacity: 1;
            transform: translate3d(0, 0, 0);
        }}
    }}

    @keyframes jitterDescEntrance {{
        0% {{
            opacity: 0;
            transform: translate3d(0, 12px, 0);
        }}
        100% {{
            opacity: 1;
            transform: translate3d(0, 0, 0);
        }}
    }}

    /* Staggered triggers when section enters viewport (120ms intervals) */
    .features-grid.is-visible .feature-card:nth-child(1) {{
        animation: jitterCardEntrance 0.85s cubic-bezier(0.16, 1, 0.3, 1) 0ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(1) .feature-card-bg {{
        animation: jitterImageEntrance 0.88s cubic-bezier(0.16, 1, 0.3, 1) 0ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(1) .feature-icon-box {{
        animation: jitterBadgeEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1) 160ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(1) .feature-heading {{
        animation: jitterHeadingEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1) 260ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(1) .feature-desc {{
        animation: jitterDescEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1) 360ms forwards;
    }}

    /* Card 02: Stagger +120ms */
    .features-grid.is-visible .feature-card:nth-child(2) {{
        animation: jitterCardEntrance 0.85s cubic-bezier(0.16, 1, 0.3, 1) 120ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(2) .feature-card-bg {{
        animation: jitterImageEntrance 0.88s cubic-bezier(0.16, 1, 0.3, 1) 120ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(2) .feature-icon-box {{
        animation: jitterBadgeEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1) 280ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(2) .feature-heading {{
        animation: jitterHeadingEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1) 380ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(2) .feature-desc {{
        animation: jitterDescEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1) 480ms forwards;
    }}

    /* Card 03: Stagger +240ms */
    .features-grid.is-visible .feature-card:nth-child(3) {{
        animation: jitterCardEntrance 0.85s cubic-bezier(0.16, 1, 0.3, 1) 240ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(3) .feature-card-bg {{
        animation: jitterImageEntrance 0.88s cubic-bezier(0.16, 1, 0.3, 1) 240ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(3) .feature-icon-box {{
        animation: jitterBadgeEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1) 400ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(3) .feature-heading {{
        animation: jitterHeadingEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1) 500ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(3) .feature-desc {{
        animation: jitterDescEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1) 600ms forwards;
    }}

    /* Card 04: Stagger +360ms */
    .features-grid.is-visible .feature-card:nth-child(4) {{
        animation: jitterCardEntrance 0.85s cubic-bezier(0.16, 1, 0.3, 1) 360ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(4) .feature-card-bg {{
        animation: jitterImageEntrance 0.88s cubic-bezier(0.16, 1, 0.3, 1) 360ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(4) .feature-icon-box {{
        animation: jitterBadgeEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1) 520ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(4) .feature-heading {{
        animation: jitterHeadingEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1) 620ms forwards;
    }}
    .features-grid.is-visible .feature-card:nth-child(4) .feature-desc {{
        animation: jitterDescEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1) 720ms forwards;
    }}

    /* Steady state locking after entrance completion */
    .features-grid.anim-completed .feature-card {{
        opacity: 1 !important;
        transform: translate3d(0, 0, 0) scale(1) !important;
        filter: blur(0px) !important;
    }}
    .features-grid.anim-completed .feature-card-bg {{
        opacity: 1 !important;
        transform: translate3d(0, 0, 0) scale(1) !important;
        filter: blur(0px) brightness(1) !important;
    }}
    .features-grid.anim-completed .feature-icon-box {{
        opacity: 1 !important;
        transform: translate3d(0, 0, 0) scale(1) !important;
    }}
    .features-grid.anim-completed .feature-heading,
    .features-grid.anim-completed .feature-desc {{
        opacity: 1 !important;
        transform: translate3d(0, 0, 0) !important;
    }}

    /* ============================================================
       SUBTLE IDLE MICRO-MOTION (2px gently on badge, 6s cycle)
       ============================================================ */
    @keyframes jitterIdleBadgeFloat {{
        0%, 100% {{
            transform: translate3d(0, 0, 0) scale(1);
        }}
        50% {{
            transform: translate3d(0, -2.5px, 0) scale(1.02);
        }}
    }}
    .features-grid.anim-completed .feature-card:nth-child(1) .feature-icon-box {{
        animation: jitterIdleBadgeFloat 6s ease-in-out infinite alternate;
        animation-delay: 0s;
    }}
    .features-grid.anim-completed .feature-card:nth-child(2) .feature-icon-box {{
        animation: jitterIdleBadgeFloat 6s ease-in-out infinite alternate;
        animation-delay: 1.5s;
    }}
    .features-grid.anim-completed .feature-card:nth-child(3) .feature-icon-box {{
        animation: jitterIdleBadgeFloat 6s ease-in-out infinite alternate;
        animation-delay: 3s;
    }}
    .features-grid.anim-completed .feature-card:nth-child(4) .feature-icon-box {{
        animation: jitterIdleBadgeFloat 6s ease-in-out infinite alternate;
        animation-delay: 4.5s;
    }}

    /* ============================================================
       DESKTOP HOVER & LIFT INTERACTION
       ============================================================ */
    @media (hover: hover) and (pointer: fine) {{
        .features-grid.anim-completed .feature-card:hover,
        .features-grid.is-visible .feature-card:hover {{
            transform: translate3d(0, -8px, 0) scale(1.02) !important;
            border-color: rgba(56, 189, 248, 0.65) !important;
            box-shadow: 0 22px 50px rgba(0, 0, 0, 0.75), 0 0 35px rgba(56, 189, 248, 0.35) !important;
        }}
        .features-grid.anim-completed .feature-card:hover .feature-icon-box {{
            animation-play-state: paused !important;
            transform: translate3d(0, -2px, 0) scale(1.04) !important;
            border-color: rgba(56, 189, 248, 0.8) !important;
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.5) !important;
        }}
    }}

    /* ============================================================
       RESPONSIVE BREAKPOINTS (FIX 05: 4 -> 2 -> 1 columns)
       ============================================================ */
    @media (max-width: 1024px) {{
        .features-grid {{
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 20px !important;
        }}
        .feature-card {{
            min-height: 280px !important;
        }}
    }}

    @media (max-width: 640px) {{
        .features-grid {{
            grid-template-columns: 1fr !important;
            gap: 16px !important;
        }}
        .feature-card {{
            min-height: 245px !important;
            padding: 20px 16px !important;
        }}
    }}

    /* Touch screen hover suppression */
    @media (hover: none) or (pointer: coarse) {{
        .feature-card:hover {{
            transform: none !important;
            box-shadow: 0 14px 35px rgba(0, 0, 0, 0.55) !important;
            border-color: rgba(255, 255, 255, 0.16) !important;
        }}
        .feature-card-bg {{
            transform: translate3d(0, 0, 0) scale(1) !important;
            filter: none !important;
        }}
    }}

    /* ============================================================
       ACCESSIBILITY (prefers-reduced-motion)
       ============================================================ */
    @media (prefers-reduced-motion: reduce) {{
        .features-grid .feature-card,
        .features-grid .feature-card-bg,
        .features-grid .feature-icon-box,
        .features-grid .feature-heading,
        .features-grid .feature-desc {{
            animation: none !important;
            transition: none !important;
            opacity: 1 !important;
            transform: none !important;
            filter: none !important;
        }}
    }}

    /* Safety fallback: ensure cards are always revealed even if script is blocked */
    @keyframes jitterSafetyReveal {{
        0% {{ opacity: 0; }}
        100% {{ opacity: 1; transform: translate3d(0, 0, 0) scale(1); filter: blur(0px); }}
    }}
    .features-grid:not(.is-visible) .feature-card {{
        animation: jitterSafetyReveal 0.6s ease-out 1.2s forwards;
    }}
    .features-grid:not(.is-visible) .feature-card-bg {{
        animation: jitterSafetyReveal 0.6s ease-out 1.2s forwards;
    }}
    .features-grid:not(.is-visible) .feature-icon-box,
    .features-grid:not(.is-visible) .feature-heading,
    .features-grid:not(.is-visible) .feature-desc {{
        animation: jitterSafetyReveal 0.6s ease-out 1.2s forwards;
    }}

    /* ============================================================
       LOGIN FORM MODAL - WHITE BACKGROUND & BLACK FONT COLOR
       ============================================================ */
    [data-testid="stDialog"] div[role="dialog"] {{
        max-width: 94vw !important;
        width: 480px !important;
        border-radius: 16px !important;
        background-color: #ffffff !important;
        background: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 25px 60px -12px rgba(0, 0, 0, 0.45) !important;
    }}

    [data-testid="stDialog"] div[role="dialog"] [data-testid="stDialogHeader"],
    [data-testid="stDialog"] div[role="dialog"] [data-testid="stDialogHeader"] h2,
    [data-testid="stDialog"] div[role="dialog"] [data-testid="stDialogTitle"],
    [data-testid="stDialog"] div[role="dialog"] h2,
    [data-testid="stDialog"] div[role="dialog"] h3 {{
        color: #000000 !important;
        font-weight: 800 !important;
    }}

    [data-testid="stDialog"] div[role="dialog"] button[aria-label="Close"] {{
        color: #334155 !important;
    }}
    [data-testid="stDialog"] div[role="dialog"] button[aria-label="Close"]:hover {{
        color: #000000 !important;
        background: #f1f5f9 !important;
    }}

    /* Labels, markdown, and text */
    [data-testid="stDialog"] div[role="dialog"] label,
    [data-testid="stDialog"] div[role="dialog"] p,
    [data-testid="stDialog"] div[role="dialog"] span,
    [data-testid="stDialog"] div[role="dialog"] [data-testid="stWidgetLabel"] p,
    [data-testid="stDialog"] div[role="dialog"] [data-testid="stWidgetLabel"] label,
    [data-testid="stDialog"] div[role="dialog"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stDialog"] div[role="dialog"] [data-testid="stMarkdownContainer"] span {{
        color: #000000 !important;
        font-weight: 600;
    }}

    /* Tabs */
    [data-testid="stDialog"] button[data-baseweb="tab"] {{
        color: #475569 !important;
        background: transparent !important;
        font-weight: 600 !important;
    }}
    [data-testid="stDialog"] button[data-baseweb="tab"][aria-selected="true"] {{
        color: #0284c7 !important;
        font-weight: 800 !important;
        border-bottom-color: #0284c7 !important;
    }}
    [data-testid="stDialog"] [data-baseweb="tab-border"] {{
        background-color: #e2e8f0 !important;
    }}
    [data-testid="stDialog"] [data-baseweb="tab-highlight"] {{
        background-color: #0284c7 !important;
    }}

    /* Radio inputs */
    [data-testid="stDialog"] [data-testid="stRadio"] label span {{
        color: #000000 !important;
        font-weight: 600 !important;
    }}

    /* Text inputs */
    [data-testid="stDialog"] div[data-baseweb="input"] {{
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }}
    [data-testid="stDialog"] input {{
        background-color: transparent !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 500 !important;
    }}
    [data-testid="stDialog"] input::placeholder {{
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
    }}
    [data-testid="stDialog"] div[data-baseweb="input"]:focus-within {{
        border-color: #0284c7 !important;
        background-color: #ffffff !important;
        box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.2) !important;
    }}

    /* Checkbox */
    [data-testid="stDialog"] [data-testid="stCheckbox"] label span {{
        color: #000000 !important;
    }}

    /* Links */
    [data-testid="stDialog"] a {{
        color: #0284c7 !important;
        font-weight: 600 !important;
        text-decoration: none !important;
    }}
    [data-testid="stDialog"] a:hover {{
        text-decoration: underline !important;
    }}

    /* Streamlit Custom Component Zero-Height Wrapper */
    iframe[title="streamlit_components.html"] {{
        position: absolute !important;
        width: 0 !important;
        height: 0 !important;
        border: none !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}
    div[data-testid="stCustomComponentV1"] {{
        margin: 0 !important;
        padding: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }}

    /* Professional Footer */
    .landing-footer {{
        text-align: center;
        padding-top: 2rem;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        color: #94a3b8;
        font-size: 0.82rem;
    }}
    .landing-footer strong {{
        color: #cbd5e1;
    }}
    </style>
    """), unsafe_allow_html=True)

    # 1. Top Navbar Row
    nav_col1, nav_col2, nav_col3 = st.columns([3.3, 1.2, 0.75])
    
    with nav_col1:
        st.markdown(clean_html("""
        <div class="landing-brand">
            <div>
                <div class="landing-brand-title">NER <span>Logistics Intelligence</span></div>
                <div class="landing-brand-sub">Accessibility & Terrain Decision Support Platform</div>
            </div>
        </div>
        """), unsafe_allow_html=True)

    with nav_col2:
        st.markdown(clean_html("""
        <div class="nav-live-wrapper">
            <span class="nav-live-pill">
                <span class="pulse-dot-live"></span>
                <span>8 NE States Live</span>
            </span>
        </div>
        """), unsafe_allow_html=True)

    with nav_col3:
        if st.button("Sign In / Log In", type="primary", use_container_width=False, key="top_nav_signin_btn"):
            render_login_modal()

    st.markdown("<div style='margin-bottom: 2.5rem;'></div>", unsafe_allow_html=True)

    # 2. Hero Section (Cinematic Typography System)
    hero_title_html = (
        '<span class="hero-title-prefix">Intelligent Mountain Logistics &amp;</span>'
        '<br>'
        '<span class="hero-title-highlight">Resilient Supply Corridors</span>'
    )
    hero_h1 = animated_heading(
        hero_title_html,
        level=1,
        anim_type="chars",
        className="hero-title",
        duration=0.95,
        stagger=0.028,
        delay=0.1,
        y=35,
        blur=8,
        once=True
    )
    hero_desc_text = (
        "An advanced spatial decision-support platform empowering field officers, Border Roads Organisation (BRO), "
        "and commercial freight transporters with real-time landslide risk telemetry, multi-modal rerouting, "
        "and essential supply prioritization across Northeast India."
    )
    hero_p = animated_paragraph(
        hero_desc_text,
        className="hero-desc",
        anim_type="words",
        duration=0.75,
        stagger=0.012,
        delay=0.55,
        y=18,
        blur=4,
        once=True
    )

    st.markdown(clean_html(f"""
    <div class="hero-container">
        {hero_h1}
        {hero_p}
    </div>
    """), unsafe_allow_html=True)

    # Hero Action Button (Centered, Compact & Sleek)
    _, btn_c, _ = st.columns([1.5, 1.2, 1.5])
    with btn_c:
        if st.button("Access Operations Console", type="primary", use_container_width=True, key="hero_access_btn"):
            render_login_modal()


    st.markdown("<div style='margin-bottom: 3rem;'></div>", unsafe_allow_html=True)

    # 3. Strategic Corridors Live Telemetry Strip
    section1_h = animated_heading(
        "Live Strategic Arterial Snapshot",
        level=3,
        anim_type="words",
        className="section-title",
        duration=0.8,
        stagger=0.03,
        y=18,
        blur=5
    )
    st.markdown(clean_html(f"""
    <div class="corridor-container">
        <div class="corridor-header">
            <div>
                {section1_h}
                <div class="corridor-sub">Real-time corridor health status across key gateways</div>
            </div>
            <div class="corridor-telemetry-status">POLLING GSAT-7A TELEMETRY</div>
        </div>
        <div class="corridor-grid">
            <div class="corridor-card" style="border:1px solid rgba(244,63,94,0.3);">
                <div class="corridor-title" style="color:#fca5a5;">NH-27 (Silchar Lifeline)</div>
                <div class="corridor-status"><span style="color:#f43f5e; font-size:0.8rem; margin-right:4px;">●</span> Severed at Km 142</div>
                <div class="corridor-detail">BRO Clearance In Progress · Bypass Active</div>
            </div>
            <div class="corridor-card" style="border:1px solid rgba(16,185,129,0.3);">
                <div class="corridor-title" style="color:#6ee7b7;">NH-15 (Tezpur-Itanagar)</div>
                <div class="corridor-status"><span style="color:#10b981; font-size:0.8rem; margin-right:4px;">●</span> 96% Optimal Flow</div>
                <div class="corridor-detail">Primary Heavy Haulier Diversion Corridor</div>
            </div>
            <div class="corridor-card" style="border:1px solid rgba(245,158,11,0.3);">
                <div class="corridor-title" style="color:#fde047;">NH-37 (Silchar-Imphal)</div>
                <div class="corridor-status"><span style="color:#f59e0b; font-size:0.8rem; margin-right:4px;">●</span> Rain Advisory</div>
                <div class="corridor-detail">Escort protocol active for night freight</div>
            </div>
            <div class="corridor-card" style="border:1px solid rgba(16,185,129,0.3);">
                <div class="corridor-title" style="color:#6ee7b7;">NH-29 (Dimapur-Kohima)</div>
                <div class="corridor-status"><span style="color:#10b981; font-size:0.8rem; margin-right:4px;">●</span> Dual Carriage Open</div>
                <div class="corridor-detail">Optimal Transit Window Monitored</div>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)

    # 4. Footer Section (Platform Capabilities & Infrastructure + Metadata)
    section2_h = animated_heading(
        "Platform Capabilities &amp; Infrastructure",
        level=2,
        anim_type="words",
        className="section-title",
        duration=0.85,
        stagger=0.035,
        y=20,
        blur=6
    )
    section2_desc = animated_paragraph(
        "Engineered to overcome severe terrain vulnerabilities, torrential monsoons, and highway blockages.",
        className="section-desc",
        anim_type="words",
        duration=0.7,
        stagger=0.015,
        delay=0.2,
        y=14,
        blur=4
    )
    st.markdown(clean_html(f"""
    <div style="text-align: center; margin-bottom: 1.8rem;">
        {section2_h}
        {section2_desc}
    </div>

    <div class="features-grid" style="margin-bottom: 3.5rem;">
        <div class="feature-card feature-card-gis">
            <div class="feature-card-bg"></div>
            <div class="feature-card-content">
                <div class="feature-icon-box">01</div>
                <h3 class="feature-heading">GIS Fleet Radar</h3>
                <p class="feature-desc">
                    Interactive real-time satellite telemetry tracking freight convoys with live highway bottleneck indicators.
                </p>
            </div>
        </div>
        <div class="feature-card feature-card-hazard">
            <div class="feature-card-bg"></div>
            <div class="feature-card-content">
                <div class="feature-icon-box">02</div>
                <h3 class="feature-heading">Terrain Hazard AI</h3>
                <p class="feature-desc">
                    Doppler precipitation modeling and IoT ground sensor integration to forecast landslide breaches on critical lifelines.
                </p>
            </div>
        </div>
        <div class="feature-card feature-card-supply">
            <div class="feature-card-bg"></div>
            <div class="feature-card-content">
                <div class="feature-icon-box">03</div>
                <h3 class="feature-heading">Supply Prioritization</h3>
                <p class="feature-desc">
                    Automated triage guaranteeing priority passage for medical cryo-oxygen, grain reserves, and aviation fuels.
                </p>
            </div>
        </div>
        <div class="feature-card feature-card-command">
            <div class="feature-card-bg"></div>
            <div class="feature-card-content">
                <div class="feature-icon-box">04</div>
                <h3 class="feature-heading">Field Command Sync</h3>
                <p class="feature-desc">
                    Unified operational console bridging Border Roads Organisation (BRO), highway police, and fleet operators.
                </p>
            </div>
        </div>
    </div>

    <footer class="landing-footer">
        <p>
            <strong>NER Logistics Accessibility Intelligence Platform</strong> · Developed for North East Regional Missions &amp; Border Logistics
        </p>
        <p style="margin-top:4px; font-size:0.75rem; color:#64748b;">
            Secure Government &amp; Fleet Data Integration · Powered by GIS Telemetry, Weather Radar &amp; Edge AI
        </p>
    </footer>
    """), unsafe_allow_html=True)

    # 5. Jitter Motion, Pointer Parallax & Cinematic Typography Controller
    components.html(r"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
    <script>
    (function() {
        /* 1. Feature Cards Jitter & Pointer Parallax Controller */
        function initJitterCards() {
            try {
                var pDoc = window.parent.document;
                if (!pDoc) return false;
                var grid = pDoc.querySelector('.features-grid');
                if (!grid) return false;

                var cards = pDoc.querySelectorAll('.feature-card');
                if (!cards || cards.length === 0) return false;

                function applySteadyState() {
                    grid.classList.add('is-visible', 'anim-completed');
                    cards.forEach(function(card) {
                        card.style.animation = 'none';
                        card.style.opacity = '1';
                        card.style.transform = 'translate3d(0, 0, 0) scale(1)';
                        card.style.filter = 'none';
                        var bg = card.querySelector('.feature-card-bg');
                        if (bg) {
                            bg.style.animation = 'none';
                            bg.style.opacity = '1';
                            bg.style.filter = 'none';
                            bg.style.transform = 'translate3d(0, 0, 0) scale(1)';
                        }
                    });
                }

                /* Handle Streamlit reruns: keep steady state if already triggered */
                if (window.parent.__nerCapabilitiesAnimated) {
                    applySteadyState();
                } else if (!grid.dataset.jitterObserved) {
                    grid.dataset.jitterObserved = 'true';
                    if ('IntersectionObserver' in window.parent) {
                        var observer = new window.parent.IntersectionObserver(function(entries, obs) {
                            entries.forEach(function(entry) {
                                if (entry.isIntersecting) {
                                    grid.classList.add('is-visible');
                                    window.parent.__nerCapabilitiesAnimated = true;
                                    obs.unobserve(entry.target);
                                    setTimeout(function() {
                                        applySteadyState();
                                    }, 1350);
                                }
                            });
                        }, { threshold: 0.2 });
                        observer.observe(grid);
                    } else {
                        applySteadyState();
                        window.parent.__nerCapabilitiesAnimated = true;
                    }
                }

                /* Smooth Mouse Parallax on Background Layer Only */
                var isTouch = ('ontouchstart' in window.parent || window.parent.navigator.maxTouchPoints > 0);
                if (!isTouch) {
                    cards.forEach(function(card) {
                        if (card.dataset.parallaxInit === 'true') return;
                        card.dataset.parallaxInit = 'true';

                        var bg = card.querySelector('.feature-card-bg');
                        if (!bg) return;

                        var rafId = null;

                        card.addEventListener('pointerenter', function() {
                            bg.style.transition = 'transform 0.15s ease-out, filter 0.4s ease-out';
                        });

                        card.addEventListener('pointermove', function(e) {
                            if (rafId) window.parent.cancelAnimationFrame(rafId);
                            rafId = window.parent.requestAnimationFrame(function() {
                                var rect = card.getBoundingClientRect();
                                var normX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
                                var normY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
                                normX = Math.max(-1, Math.min(1, normX));
                                normY = Math.max(-1, Math.min(1, normY));
                                var px = (normX * 6.5).toFixed(1);
                                var py = (normY * 6.5).toFixed(1);
                                bg.style.transition = 'transform 0.08s ease-out, filter 0.4s ease-out';
                                bg.style.transform = 'translate3d(' + px + 'px, ' + py + 'px, 0) scale(1.05)';
                            });
                        });

                        card.addEventListener('pointerleave', function() {
                            if (rafId) window.parent.cancelAnimationFrame(rafId);
                            bg.style.transition = 'transform 0.45s cubic-bezier(0.16, 1, 0.3, 1), filter 0.4s ease-out';
                            bg.style.transform = 'translate3d(0px, 0px, 0) scale(1)';
                        });
                    });
                }
                return true;
            } catch(e) {
                return false;
            }
        }

        /* 2. Client-Side Cinematic Typography Controller */
        function initTypographyAnimations() {
            try {
                var pDoc = window.parent.document;
                var pWin = window.parent;
                if (!pDoc || !pWin) return false;
                
                var gs = window.gsap || pWin.gsap;
                if (!gs) return false;

                /* Respect prefers-reduced-motion */
                var prefersReduced = pWin.matchMedia && pWin.matchMedia('(prefers-reduced-motion: reduce)').matches;

                /* Helper to recursively split text nodes into words / chars while preserving tags & spaces */
                function splitNode(node, animType) {
                    if (node.nodeType === Node.TEXT_NODE) {
                        var text = node.textContent;
                        if (!text || text.trim() === '') return null;
                        var fragment = pDoc.createDocumentFragment();
                        var parts = text.split(/(\s+)/);
                        for (var i = 0; i < parts.length; i++) {
                            var part = parts[i];
                            if (/^\s+$/.test(part)) {
                                fragment.appendChild(pDoc.createTextNode(part));
                            } else if (part.length > 0) {
                                var wordSpan = pDoc.createElement('span');
                                wordSpan.className = 'split-word';
                                if (animType === 'chars') {
                                    for (var c = 0; c < part.length; c++) {
                                        var charSpan = pDoc.createElement('span');
                                        charSpan.className = 'split-char';
                                        charSpan.textContent = part[c];
                                        wordSpan.appendChild(charSpan);
                                    }
                                } else {
                                    wordSpan.textContent = part;
                                }
                                fragment.appendChild(wordSpan);
                            }
                        }
                        return fragment;
                    } else if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.tagName.toLowerCase() === 'br') return null;
                        var children = Array.from(node.childNodes);
                        for (var j = 0; j < children.length; j++) {
                            var rep = splitNode(children[j], animType);
                            if (rep) {
                                node.replaceChild(rep, children[j]);
                            }
                        }
                        return null;
                    }
                    return null;
                }

                /* --- HERO SECTION ANIMATION --- */
                var heroTitle = pDoc.querySelector('.hero-title[data-anim-typography="true"]');
                var heroDesc = pDoc.querySelector('.hero-desc[data-anim-typography="true"]');
                var heroBtnWrap = pDoc.querySelector('div.st-key-hero_access_btn');
                var heroBtn = heroBtnWrap ? heroBtnWrap.querySelector('button') : null;

                if (heroTitle && !heroTitle.dataset.animInitialized) {
                    heroTitle.dataset.animInitialized = 'true';

                    if (prefersReduced || pWin.__nerTypographyAnimated) {
                        heroTitle.style.opacity = '1';
                        if (heroDesc) heroDesc.style.opacity = '1';
                        if (heroBtn) heroBtn.style.opacity = '1';
                    } else {
                        /* Split ONLY the prefix into characters to eliminate ghost duplication on the highlight gradient */
                        var prefixEl = heroTitle.querySelector('.hero-title-prefix');
                        var highlightEl = heroTitle.querySelector('.hero-title-highlight');

                        if (prefixEl) {
                            splitNode(prefixEl, 'chars');
                        }
                        var prefixChars = prefixEl ? prefixEl.querySelectorAll('.split-char') : [];

                        /* Split Description into Words */
                        var words = [];
                        if (heroDesc) {
                            heroDesc.dataset.animInitialized = 'true';
                            splitNode(heroDesc, 'words');
                            words = heroDesc.querySelectorAll('.split-word');
                        }

                        var isMobile = (pWin.innerWidth <= 640);
                        var charY = isMobile ? 18 : 34;
                        var charBlur = isMobile ? 4 : 8;
                        var charStagger = isMobile ? 0.016 : 0.026;
                        var charDuration = isMobile ? 0.75 : 0.95;

                        /* Initial states */
                        if (prefixChars.length > 0) {
                            gs.set(prefixChars, { opacity: 0, y: charY, filter: 'blur(' + charBlur + 'px)' });
                        }
                        if (highlightEl) {
                            gs.set(highlightEl, { opacity: 0, y: isMobile ? 16 : 26, filter: 'blur(4px)' });
                        }
                        if (words.length > 0) {
                            gs.set(words, { opacity: 0, y: isMobile ? 12 : 16, filter: 'blur(4px)' });
                        }
                        if (heroBtn) {
                            gs.set(heroBtn, { opacity: 0, y: 16 });
                        }

                        /* Hero Cinematic Entrance Timeline */
                        var tl = gs.timeline({
                            delay: 0.12,
                            onComplete: function() {
                                if (prefixChars.length > 0) {
                                    gs.set(prefixChars, { clearProps: "transform,opacity,filter,willChange" });
                                }
                                if (highlightEl) {
                                    gs.set(highlightEl, { clearProps: "transform,opacity,filter,willChange" });
                                }
                                if (words.length > 0) {
                                    gs.set(words, { clearProps: "transform,opacity,filter,willChange" });
                                }
                                if (heroBtn) {
                                    gs.set(heroBtn, { clearProps: "transform,opacity,willChange" });
                                }
                                pWin.__nerTypographyAnimated = true;
                            }
                        });

                        if (prefixChars.length > 0) {
                            tl.to(prefixChars, {
                                opacity: 1,
                                y: 0,
                                filter: "blur(0px)",
                                duration: charDuration,
                                stagger: charStagger,
                                ease: "power3.out"
                            });
                        }

                        if (highlightEl) {
                            tl.to(highlightEl, {
                                opacity: 1,
                                y: 0,
                                filter: "blur(0px)",
                                duration: 0.8,
                                ease: "power3.out"
                            }, "-=0.45");
                        }

                        if (words.length > 0) {
                            tl.to(words, {
                                opacity: 1,
                                y: 0,
                                filter: "blur(0px)",
                                duration: 0.72,
                                stagger: 0.012,
                                ease: "power2.out"
                            }, "-=0.52");
                        }

                        if (heroBtn) {
                            tl.to(heroBtn, {
                                opacity: 1,
                                y: 0,
                                duration: 0.6,
                                ease: "power2.out"
                            }, "-=0.35");
                        }
                    }
                }

                /* --- SECTION HEADINGS SCROLL-IN ANIMATION --- */
                var otherHeadings = pDoc.querySelectorAll('[data-anim-typography="true"]:not(.hero-title):not(.hero-desc)');
                otherHeadings.forEach(function(h) {
                    if (h.dataset.animInitialized === 'true') return;
                    h.dataset.animInitialized = 'true';

                    var animType = h.dataset.animType || 'words';
                    splitNode(h, animType);
                    var targets = animType === 'chars' ? h.querySelectorAll('.split-char') : h.querySelectorAll('.split-word');

                    if (prefersReduced || pWin.__nerTypographyAnimated) {
                        gs.set(targets, { opacity: 1, y: 0, filter: 'none' });
                        return;
                    }

                    gs.set(targets, { opacity: 0, y: 18, filter: 'blur(5px)' });

                    if ('IntersectionObserver' in pWin) {
                        var obs = new pWin.IntersectionObserver(function(entries, observer) {
                            entries.forEach(function(entry) {
                                if (entry.isIntersecting) {
                                    gs.to(targets, {
                                        opacity: 1,
                                        y: 0,
                                        filter: 'blur(0px)',
                                        duration: 0.8,
                                        stagger: 0.024,
                                        ease: "power3.out",
                                        onComplete: function() {
                                            gs.set(targets, { clearProps: "transform,opacity,filter" });
                                        }
                                    });
                                    observer.unobserve(entry.target);
                                }
                            });
                        }, { threshold: 0.2 });
                        obs.observe(h);
                    } else {
                        gs.to(targets, { opacity: 1, y: 0, filter: 'none', duration: 0.5 });
                    }
                });

                return true;
            } catch(err) {
                return false;
            }
        }

        /* Continuous Poller for Streamlit mounting */
        function runPollers() {
            initJitterCards();
            initTypographyAnimations();
        }

        runPollers();
        var attempts = 0;
        var poller = setInterval(function() {
            attempts++;
            runPollers();
            if (attempts > 25) {
                clearInterval(poller);
            }
        }, 150);
    })();
    </script>
    """, height=0, width=0)



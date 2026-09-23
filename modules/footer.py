import streamlit as st

def clean_html(html_str):
    """
    Strips leading and trailing whitespace from every line so that
    Streamlit's markdown renderer never interprets lines as indented code blocks.
    """
    return "\n".join(line.strip() for line in html_str.splitlines() if line.strip())

def render_app_footer():
    """
    Renders the unified enterprise footer across all authenticated internal application pages.
    Matches the official reference design:
    - 5-column layout: Brand/About | Quick Links | Resources | Contact Us | Follow Us
    - Subtle blue divider lines (vertical between columns, horizontal above copyright)
    - Dark background with white/light text and cyan accents
    - Normal document flow (no fixed/sticky positioning, no overlap)
    - Full responsiveness with clean mobile reflow
    """
    footer_html = """
    <style>
    /* =========================================================
       SHARED APPLICATION FOOTER STYLES
       ========================================================= */
    /* Ensure Streamlit containers enclosing the footer do not constrain width or add side/bottom padding */
    div[data-testid="element-container"]:has(.app-footer-wrapper),
    div[data-testid="stElementContainer"]:has(.app-footer-wrapper),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.app-footer-wrapper) {
        width: 100% !important;
        max-width: 100% !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-bottom: 0 !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        margin-bottom: 0 !important;
        box-sizing: border-box !important;
    }

    .stApp:has(.app-footer-wrapper) .block-container,
    .stApp:has(.app-footer-wrapper) .stMainBlockContainer {
        padding-bottom: 0 !important;
    }

    .app-footer-wrapper {
        position: relative !important;
        width: 100vw !important;
        left: 50% !important;
        right: 50% !important;
        margin-left: -50vw !important;
        margin-right: -50vw !important;
        margin-top: 56px !important;
        margin-bottom: 0px !important;
        padding: 0 !important;
        background: #030712 !important;
        border-top: 1px solid rgba(56, 189, 248, 0.18) !important;
        box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.45) !important;
        color: #94a3b8;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    .app-footer-container {
        max-width: 1360px;
        margin: 0 auto;
        padding: 38px 24px 28px 24px;
        box-sizing: border-box;
    }

    .app-footer-columns {
        display: flex;
        flex-direction: row;
        align-items: stretch;
        justify-content: space-between;
        gap: 0;
        width: 100%;
    }

    /* Individual Column Sizing and Vertical Divider Lines */
    .footer-col {
        box-sizing: border-box;
        padding: 0 24px;
        border-right: 1px solid rgba(56, 189, 248, 0.18);
    }

    .footer-col:first-child {
        padding-left: 0;
        flex: 1.35;
        max-width: 320px;
    }

    .footer-col:nth-child(2) {
        flex: 0.9;
    }

    .footer-col:nth-child(3) {
        flex: 0.95;
    }

    .footer-col:nth-child(4) {
        flex: 1.15;
    }

    .footer-col:last-child {
        padding-right: 0;
        border-right: none;
        flex: 0.85;
    }

    /* Brand / About Column */
    .footer-brand-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
    }

    .footer-brand-emblem {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: rgba(2, 132, 199, 0.18);
        border: 1.2px solid rgba(56, 189, 248, 0.6);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.35);
        flex-shrink: 0;
    }

    .footer-brand-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        line-height: 1.2;
    }

    .footer-brand-title .ner-accent {
        color: #38bdf8;
    }

    .footer-brand-title .title-text {
        color: #ffffff;
    }

    .footer-brand-sub {
        font-size: 0.74rem;
        font-weight: 500;
        color: #94a3b8;
        line-height: 1.3;
        margin-bottom: 16px;
    }

    .footer-brand-desc {
        font-size: 0.81rem;
        line-height: 1.55;
        color: #94a3b8;
        margin: 0;
    }

    /* Column Section Headings */
    .footer-col-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.95rem;
        font-weight: 700;
        color: #ffffff;
        margin-top: 0;
        margin-bottom: 14px;
        letter-spacing: 0.01em;
    }

    /* Link Lists */
    .footer-links {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .footer-links li {
        margin-bottom: 7px;
        line-height: 1.4;
    }

    .footer-link-item {
        color: #94a3b8;
        text-decoration: none;
        font-size: 0.82rem;
        font-weight: 500;
        transition: color 0.18s ease;
        display: inline-block;
    }

    .footer-link-item:hover {
        color: #38bdf8;
        text-decoration: none;
    }

    /* Contact Details */
    .footer-contact-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 2px;
    }

    .footer-contact-row {
        display: flex;
        align-items: center;
        gap: 9px;
        font-size: 0.82rem;
        color: #cbd5e1;
        text-decoration: none;
        transition: color 0.18s ease;
    }

    .footer-contact-row:hover {
        color: #38bdf8;
        text-decoration: none;
    }

    .footer-contact-icon {
        color: #38bdf8;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    /* Follow Us Social Icons */
    .footer-social-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 4px;
    }

    .footer-social-btn {
        width: 28px;
        height: 28px;
        border-radius: 5px;
        background: #2563eb;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        text-decoration: none;
        transition: all 0.2s ease;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3);
    }

    .footer-social-btn:hover {
        background: #38bdf8;
        color: #030712;
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(56, 189, 248, 0.45);
    }

    /* Horizontal Divider & Copyright Bar */
    .footer-copyright-bar {
        border-top: 1px solid rgba(56, 189, 248, 0.18);
        padding: 16px 24px;
        text-align: center;
        font-size: 0.78rem;
        color: #64748b;
        background: #020617;
    }

    /* =========================================================
       RESPONSIVE BREAKPOINTS
       ========================================================= */
    @media (max-width: 1024px) {
        .app-footer-columns {
            flex-wrap: wrap;
            gap: 24px 0;
        }
        .footer-col {
            padding: 0 16px;
        }
        .footer-col:first-child {
            flex: 1 1 100%;
            max-width: 100%;
            border-right: none;
            border-bottom: 1px solid rgba(56, 189, 248, 0.12);
            padding-bottom: 20px;
        }
        .footer-col:nth-child(2),
        .footer-col:nth-child(3),
        .footer-col:nth-child(4) {
            flex: 1 1 calc(33.333% - 1px);
        }
        .footer-col:last-child {
            flex: 1 1 100%;
            border-top: 1px solid rgba(56, 189, 248, 0.12);
            padding-top: 18px;
            padding-left: 0;
        }
    }

    @media (max-width: 768px) {
        .app-footer-container {
            padding: 28px 16px 20px 16px;
        }
        .app-footer-columns {
            flex-direction: column;
            gap: 20px 0;
        }
        .footer-col {
            border-right: none !important;
            padding: 0 0 16px 0 !important;
            border-bottom: 1px solid rgba(56, 189, 248, 0.12);
            flex: 1 1 100% !important;
            max-width: 100% !important;
        }
        .footer-col:last-child {
            border-bottom: none;
            padding-bottom: 0 !important;
        }
    }
    </style>

    <footer class="app-footer-wrapper" role="contentinfo">
      <div class="app-footer-container">
        <div class="app-footer-columns">
          
          <!-- 1. BRAND / ABOUT -->
          <div class="footer-col">
            <div class="footer-brand-header">
              <span class="footer-brand-emblem">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10" stroke="#38bdf8" stroke-opacity="0.9"/>
                  <polygon points="12 3 14 10 21 12 14 14 12 21 10 14 3 12 10 10" fill="rgba(56,189,248,0.3)" stroke="#38bdf8"/>
                </svg>
              </span>
              <div class="footer-brand-title">
                <span class="ner-accent">NER</span> <span class="title-text">Logistics Intelligence</span>
              </div>
            </div>
            <div class="footer-brand-sub">
              Accessibility Intelligence Platform - Northeast Mission
            </div>
            <p class="footer-brand-desc">
              Real-time intelligence for safer, faster and more resilient logistics operations across the Northeast.
            </p>
          </div>

          <!-- 2. QUICK LINKS -->
          <div class="footer-col">
            <h4 class="footer-col-title">Quick Links</h4>
            <ul class="footer-links">
              <li><a href="?nav=home" class="footer-link-item" target="_self">Home</a></li>
              <li><a href="?nav=gis" class="footer-link-item" target="_self">GIS Fleet</a></li>
              <li><a href="?nav=weather" class="footer-link-item" target="_self">Weather AI</a></li>
              <li><a href="?nav=supply" class="footer-link-item" target="_self">Supply & Cargo</a></li>
              <li><a href="?nav=field_ops" class="footer-link-item" target="_self">Field Ops</a></li>
              <li><a href="?nav=route_optimizer" class="footer-link-item" target="_self">AI Router</a></li>
            </ul>
          </div>

          <!-- 3. RESOURCES -->
          <div class="footer-col">
            <h4 class="footer-col-title">Resources</h4>
            <ul class="footer-links">
              <li><a href="#help" class="footer-link-item">Help & Support</a></li>
              <li><a href="#guide" class="footer-link-item">User Guide</a></li>
              <li><a href="#privacy" class="footer-link-item">Privacy Policy</a></li>
              <li><a href="#terms" class="footer-link-item">Terms of Service</a></li>
              <li><a href="#contact" class="footer-link-item">Contact Us</a></li>
            </ul>
          </div>

          <!-- 4. CONTACT US -->
          <div class="footer-col">
            <h4 class="footer-col-title">Contact Us</h4>
            <div class="footer-contact-list">
              <a href="mailto:support@nerlogistics.gov.in" class="footer-contact-row">
                <span class="footer-contact-icon">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                    <polyline points="22,6 12,13 2,6"/>
                  </svg>
                </span>
                <span>support@nerlogistics.gov.in</span>
              </a>
              <div class="footer-contact-row">
                <span class="footer-contact-icon">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                    <circle cx="12" cy="10" r="3"/>
                  </svg>
                </span>
                <span>Guwahati, Assam, India</span>
              </div>
            </div>
          </div>

          <!-- 5. FOLLOW US -->
          <div class="footer-col">
            <h4 class="footer-col-title">Follow Us</h4>
            <div class="footer-social-row">
              <!-- LinkedIn -->
              <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" class="footer-social-btn" aria-label="LinkedIn" title="LinkedIn">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="#ffffff">
                  <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                </svg>
              </a>

              <!-- X / Twitter -->
              <a href="https://x.com" target="_blank" rel="noopener noreferrer" class="footer-social-btn" aria-label="X" title="X">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="#ffffff">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
              </a>

              <!-- YouTube -->
              <a href="https://youtube.com" target="_blank" rel="noopener noreferrer" class="footer-social-btn" aria-label="YouTube" title="YouTube">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="#ffffff">
                  <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/>
                </svg>
              </a>

              <!-- Facebook -->
              <a href="https://facebook.com" target="_blank" rel="noopener noreferrer" class="footer-social-btn" aria-label="Facebook" title="Facebook">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="#ffffff">
                  <path d="M9 8h-3v4h3v12h5v-12h3.642l.358-4h-4v-1.667c0-.955.192-1.333 1.115-1.333h2.885v-5h-3.808c-3.596 0-5.192 1.583-5.192 4.615v3.385z"/>
                </svg>
              </a>
            </div>
          </div>

        </div>
      </div>

      <!-- COPYRIGHT ROW -->
      <div class="footer-copyright-bar">
        © All Rights Reserved
      </div>
    </footer>
    """
    st.markdown(clean_html(footer_html), unsafe_allow_html=True)

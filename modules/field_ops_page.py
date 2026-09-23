import streamlit as st
import pandas as pd
import pydeck as pdk
import folium
from branca.element import MacroElement, Template
from streamlit_folium import st_folium
import networkx as nx
import os
import streamlit.components.v1 as components
from streamlit_geolocation import streamlit_geolocation

import json
import time
from datetime import datetime
from modules.auth_session import get_authenticated_user

_gps_component_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gps_component")
_realtime_gps_tracker = components.declare_component("realtime_gps_tracker", path=_gps_component_dir)

# Persistent JSON Storage Setup
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
os.makedirs(_DATA_DIR, exist_ok=True)
_PENDING_REPORTS_FILE = os.path.join(_DATA_DIR, "pending_offline_reports.json")
_SYNCED_REPORTS_FILE = os.path.join(_DATA_DIR, "synchronized_reports.json")
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

def _save_public_help_requests(requests_list):
    os.makedirs(_DATA_DIR, exist_ok=True)
    temp_file = _HELP_REQUESTS_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(requests_list, f, indent=2)
        os.replace(temp_file, _HELP_REQUESTS_FILE)
        return True
    except Exception:
        try:
            with open(_HELP_REQUESTS_FILE, "w", encoding="utf-8") as f:
                json.dump(requests_list, f, indent=2)
            return True
        except Exception:
            return False

def _accept_public_help_request(help_request_id, officer_name="Field Officer", officer_id="FO-DISPATCH"):
    requests_list = _load_public_help_requests()
    updated = False
    for req in requests_list:
        if req.get("help_request_id") == help_request_id:
            req["status"] = "ACCEPTED"
            req["handled"] = True
            req["accepted_by"] = officer_name
            req["accepted_by_id"] = officer_id
            req["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated = True
            break
    if updated:
        _save_public_help_requests(requests_list)
        if "public_help_requests" in st.session_state and isinstance(st.session_state.public_help_requests, list):
            for s_req in st.session_state.public_help_requests:
                if s_req.get("help_request_id") == help_request_id:
                    s_req["status"] = "ACCEPTED"
                    s_req["handled"] = True
                    s_req["accepted_by"] = officer_name
                    s_req["accepted_by_id"] = officer_id
                    s_req["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
    return updated

# Ensure persistent JSON storage files exist with valid initial empty lists
for _filepath in [_PENDING_REPORTS_FILE, _SYNCED_REPORTS_FILE, _HELP_REQUESTS_FILE]:

    if not os.path.exists(_filepath):
        try:
            with open(_filepath, "w", encoding="utf-8") as _f:
                json.dump([], _f)
        except Exception:
            pass

def _load_pending_reports():
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.exists(_PENDING_REPORTS_FILE):
        _save_pending_reports([])
        return []
    try:
        with open(_PENDING_REPORTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def _save_pending_reports(reports):
    os.makedirs(_DATA_DIR, exist_ok=True)
    temp_file = _PENDING_REPORTS_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(reports, f, indent=2)
        os.replace(temp_file, _PENDING_REPORTS_FILE)
        return True
    except Exception:
        try:
            with open(_PENDING_REPORTS_FILE, "w", encoding="utf-8") as f:
                json.dump(reports, f, indent=2)
            return True
        except Exception:
            return False

def _load_synced_reports():
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.exists(_SYNCED_REPORTS_FILE):
        _save_synced_reports([])
        return []
    try:
        with open(_SYNCED_REPORTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def _save_synced_reports(reports):
    os.makedirs(_DATA_DIR, exist_ok=True)
    temp_file = _SYNCED_REPORTS_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(reports, f, indent=2)
        os.replace(temp_file, _SYNCED_REPORTS_FILE)
        return True
    except Exception:
        try:
            with open(_SYNCED_REPORTS_FILE, "w", encoding="utf-8") as f:
                json.dump(reports, f, indent=2)
            return True
        except Exception:
            return False

def _sync_offline_reports():
    """
    Safely and idempotently synchronizes all pending offline reports to synchronized storage.
    Ensures zero data loss, no duplicate reports, and only clears pending storage
    after confirmed successful write to synchronized storage.
    """
    pending = _load_pending_reports()
    if not pending:
        return 0, []
    
    synced = _load_synced_reports()
    existing_ids = {r.get("report_id") for r in synced if r.get("report_id")}
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    synced_reports = []
    
    for r in pending:
        r_copy = dict(r)
        r_copy["status"] = "Synchronized"
        if not r_copy.get("synced_at"):
            r_copy["synced_at"] = now_str
        if r_copy.get("report_id") not in existing_ids:
            synced.append(r_copy)
            existing_ids.add(r_copy.get("report_id"))
        synced_reports.append(r_copy)
    
    # Save to synchronized storage first
    if _save_synced_reports(synced):
        # Only clear pending queue after confirmed successful write
        _save_pending_reports([])
        return len(synced_reports), synced_reports
    else:
        return 0, []

class LeafletInteractiveMapTools(MacroElement):
    """
    Client-side Leaflet extension providing interactive Pointer and Eraser tools
    with live coordinate display and zero-rerun performance.
    """
    def __init__(self):
        super().__init__()
        self._template = Template("""
            {% macro header(this, kwargs) %}
                <style>
                    /* Map frame border */
                    .folium-map {
                        border-radius: 10px !important;
                        overflow: hidden !important;
                        border: 1.5px solid rgba(32, 196, 255, 0.35) !important;
                    }

                    /* Floating HUD Toolbar & Coordinates */
                    .fo-map-hud-container {
                        position: absolute;
                        top: 14px;
                        right: 14px;
                        z-index: 1000;
                        display: flex;
                        flex-direction: column;
                        gap: 10px;
                        align-items: flex-end;
                        pointer-events: auto;
                        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    }

                    /* Tool Selector Buttons */
                    .fo-map-tool-group {
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        background: rgba(4, 20, 44, 0.94);
                        border: 1.5px solid rgba(32, 196, 255, 0.45);
                        border-radius: 10px;
                        padding: 6px 10px;
                        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.6);
                        backdrop-filter: blur(8px);
                    }

                    .fo-tool-btn {
                        background: rgba(15, 23, 42, 0.85);
                        border: 1px solid rgba(255, 255, 255, 0.18);
                        border-radius: 7px;
                        color: rgba(255, 255, 255, 0.85);
                        font-size: 0.86rem;
                        font-weight: 700;
                        padding: 7px 15px;
                        cursor: pointer;
                        display: inline-flex;
                        align-items: center;
                        gap: 6px;
                        transition: all 0.2s ease;
                        user-select: none;
                        outline: none;
                    }

                    .fo-tool-btn:hover {
                        border-color: #20C4FF;
                        color: #FFFFFF;
                        box-shadow: 0 0 10px rgba(32, 196, 255, 0.35);
                    }

                    .fo-tool-btn.active-pointer {
                        background: rgba(32, 196, 255, 0.25);
                        border-color: #20C4FF;
                        color: #FFFFFF;
                        box-shadow: 0 0 14px rgba(32, 196, 255, 0.5);
                    }

                    .fo-tool-btn.active-eraser {
                        background: rgba(239, 68, 68, 0.26);
                        border-color: #EF4444;
                        color: #FFFFFF;
                        box-shadow: 0 0 14px rgba(239, 68, 68, 0.5);
                    }

                    /* Coordinate Display Panel */
                    .fo-coord-card {
                        background: rgba(4, 20, 44, 0.95);
                        border: 1.5px solid rgba(32, 196, 255, 0.45);
                        border-radius: 10px;
                        padding: 12px 16px;
                        width: 220px;
                        box-sizing: border-box;
                        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.65);
                        backdrop-filter: blur(8px);
                        display: none;
                        animation: foFadeIn 0.2s ease;
                    }

                    @keyframes foFadeIn {
                        from { opacity: 0; transform: translateY(-4px); }
                        to { opacity: 1; transform: translateY(0); }
                    }

                    .fo-coord-title {
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        font-size: 0.84rem;
                        font-weight: 800;
                        color: #20C4FF;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                        margin-bottom: 8px;
                        border-bottom: 1px solid rgba(32, 196, 255, 0.25);
                        padding-bottom: 5px;
                    }

                    .fo-coord-row {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        font-size: 0.84rem;
                        line-height: 1.55;
                        color: #E2E8F0;
                    }

                    .fo-coord-label {
                        color: rgba(255, 255, 255, 0.72);
                        font-weight: 600;
                    }

                    .fo-coord-val {
                        color: #38BDF8;
                        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                        font-weight: 700;
                        letter-spacing: 0.02em;
                    }

                    /* Cursor styles */
                    .fo-mode-pointer {
                        cursor: crosshair !important;
                    }
                    .fo-mode-pointer .leaflet-grab,
                    .fo-mode-pointer .leaflet-interactive {
                        cursor: crosshair !important;
                    }
                    .fo-mode-eraser {
                        cursor: cell !important;
                    }

                    /* Custom pin styling */
                    .fo-custom-pin {
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        cursor: pointer;
                        transition: transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
                    }
                    .fo-custom-pin:hover {
                        transform: scale(1.2) translateY(-2px);
                    }
                    .fo-custom-pin.active-selected svg {
                        filter: drop-shadow(0 0 10px #20C4FF) drop-shadow(0 4px 10px rgba(0, 0, 0, 0.7));
                    }
                </style>
            {% endmacro %}

            {% macro html(this, kwargs) %}
                <div id="fo-hud-container" class="fo-map-hud-container">
                    <div class="fo-map-tool-group">
                        <button type="button" id="fo-btn-pointer" class="fo-tool-btn active-pointer" title="Pointer Mode: Click anywhere on the map to place a pin and see coordinates">
                            <span>📍</span> Pointer
                        </button>
                        <button type="button" id="fo-btn-eraser" class="fo-tool-btn" title="Eraser Mode: Click any user pointer to erase it">
                            <span>⌫</span> Eraser
                        </button>
                    </div>

                    <div id="fo-coord-card" class="fo-coord-card">
                        <div class="fo-coord-title">
                            <span>📍</span> Selected Location
                        </div>
                        <div class="fo-coord-row">
                            <span class="fo-coord-label">Latitude:</span>
                            <span id="fo-val-lat" class="fo-coord-val">--</span>
                        </div>
                        <div class="fo-coord-row">
                            <span class="fo-coord-label">Longitude:</span>
                            <span id="fo-val-lon" class="fo-coord-val">--</span>
                        </div>
                    </div>
                </div>
            {% endmacro %}

            {% macro script(this, kwargs) %}
                (function() {
                    var map = {{this._parent.get_name()}};
                    if (!map) return;

                    var currentMode = 'pointer'; // 'pointer' or 'eraser'
                    var userPointers = []; // array of { id, marker, lat, lng }
                    var selectedPointer = null;
                    var nextId = 1;

                    var hud = document.getElementById('fo-hud-container');
                    var btnPointer = document.getElementById('fo-btn-pointer');
                    var btnEraser = document.getElementById('fo-btn-eraser');
                    var coordCard = document.getElementById('fo-coord-card');
                    var valLat = document.getElementById('fo-val-lat');
                    var valLon = document.getElementById('fo-val-lon');

                    // Prevent click & scroll propagation from toolbar to map
                    if (hud) {
                        L.DomEvent.disableClickPropagation(hud);
                        L.DomEvent.disableScrollPropagation(hud);
                    }

                    function updateCursor() {
                        var container = map.getContainer();
                        if (!container) return;
                        if (currentMode === 'pointer') {
                            container.classList.add('fo-mode-pointer');
                            container.classList.remove('fo-mode-eraser');
                        } else {
                            container.classList.add('fo-mode-eraser');
                            container.classList.remove('fo-mode-pointer');
                        }
                    }
                    updateCursor();

                    function setMode(mode) {
                        currentMode = mode;
                        if (mode === 'pointer') {
                            btnPointer.classList.add('active-pointer');
                            btnEraser.classList.remove('active-eraser');
                        } else {
                            btnEraser.classList.add('active-eraser');
                            btnPointer.classList.remove('active-pointer');
                        }
                        updateCursor();
                    }

                    if (btnPointer) {
                        btnPointer.addEventListener('click', function(e) {
                            L.DomEvent.stopPropagation(e);
                            setMode('pointer');
                        });
                    }

                    if (btnEraser) {
                        btnEraser.addEventListener('click', function(e) {
                            L.DomEvent.stopPropagation(e);
                            setMode('eraser');
                        });
                    }

                    function updateCoordDisplay(lat, lng) {
                        if (coordCard && valLat && valLon) {
                            valLat.textContent = Number(lat).toFixed(6);
                            valLon.textContent = Number(lng).toFixed(6);
                            coordCard.style.display = 'block';
                        }
                    }

                    function clearCoordDisplay() {
                        if (coordCard) {
                            coordCard.style.display = 'none';
                        }
                    }

                    function selectPointer(p) {
                        selectedPointer = p;
                        userPointers.forEach(function(item) {
                            var el = item.marker.getElement();
                            if (el) {
                                if (item === p) {
                                    el.classList.add('active-selected');
                                } else {
                                    el.classList.remove('active-selected');
                                }
                            }
                        });
                        updateCoordDisplay(p.lat, p.lng);
                    }

                    function removePointer(p) {
                        map.removeLayer(p.marker);
                        var idx = userPointers.indexOf(p);
                        if (idx > -1) {
                            userPointers.splice(idx, 1);
                        }
                        if (selectedPointer === p) {
                            if (userPointers.length > 0) {
                                selectPointer(userPointers[userPointers.length - 1]);
                            } else {
                                selectedPointer = null;
                                clearCoordDisplay();
                            }
                        }
                    }

                    function createPinIcon() {
                        var svgHtml = '<svg width="28" height="38" viewBox="0 0 28 38" fill="none" xmlns="http://www.w3.org/2000/svg">' +
                            '<path d="M14 0C6.26801 0 0 6.26801 0 14C0 24.5 14 38 14 38C14 38 28 24.5 28 14C28 6.26801 21.732 0 14 0Z" fill="#20C4FF" filter="drop-shadow(0 3px 6px rgba(0,0,0,0.5))"/>' +
                            '<circle cx="14" cy="14" r="5.5" fill="#04142C"/>' +
                            '<circle cx="14" cy="14" r="2.8" fill="#FFFFFF"/>' +
                            '</svg>';
                        return L.divIcon({
                            className: 'fo-custom-pin',
                            html: svgHtml,
                            iconSize: [28, 38],
                            iconAnchor: [14, 38]
                        });
                    }

                    // Forward PolyLine clicks directly to map click handler
                    setTimeout(function() {
                        map.eachLayer(function(layer) {
                            if (layer instanceof L.PolyLine && !(layer instanceof L.Polygon)) {
                                layer.on('click', function(e) {
                                    if (currentMode === 'pointer') {
                                        map.fire('click', e);
                                    }
                                });
                            }
                        });
                    }, 350);

                    // Leaflet Map Click Handler
                    map.on('click', function(e) {
                        if (currentMode === 'pointer') {
                            var lat = e.latlng.lat;
                            var lng = e.latlng.lng;

                            var marker = L.marker([lat, lng], {
                                icon: createPinIcon(),
                                riseOnHover: true
                            }).addTo(map);

                            var pointerObj = {
                                id: nextId++,
                                marker: marker,
                                lat: lat,
                                lng: lng
                            };

                            marker.on('click', function(evt) {
                                L.DomEvent.stopPropagation(evt);
                                if (currentMode === 'eraser') {
                                    removePointer(pointerObj);
                                } else {
                                    selectPointer(pointerObj);
                                }
                            });

                            userPointers.push(pointerObj);
                            selectPointer(pointerObj);
                        }
                    });
                })();
            {% endmacro %}
        """)

def render_field_ops_page():
    # PART 7 — FIELD OFFICER INCIDENT REPORTING
    # ============================================================
    
    st.markdown("""
    <style>
    /* ============================================================
       FIELD OPS DESIGN SYSTEM — SOLID DEEP NAVY COMMAND PANELS
       Strictly scoped to Field Ops via .field-ops-panel-marker
       and .field-ops-submit-wrap. Zero global impact.
       ============================================================ */

    /* Main Page Header: Centered with Cyan Accent */
    .fo-header-container {
        text-align: center;
        margin: 1.75rem auto 2.25rem auto;
        max-width: 900px;
        padding: 0 1rem;
        background: transparent !important;
        background-color: transparent !important;
    }
    .fo-main-title {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        line-height: 1.25;
        color: #20C4FF;
        text-shadow: 0 0 20px rgba(32, 196, 255, 0.4);
        margin: 0 0 0.5rem 0;
        text-align: center;
        text-transform: uppercase;
    }
    .fo-sub-description {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 0.98rem;
        color: #FFFFFF;
        opacity: 0.92;
        line-height: 1.5;
        margin: 0 auto;
        text-align: center;
    }

    /* ============================================================
       FIELD OPS PAGE CONTAINMENT
       Guarantee that the page root block stays completely transparent
       so that the scenic mountain/truck wallpaper is 100% visible
       outside and between the panels. Zero page-level blue overlay.
       ============================================================ */
    .block-container > div[data-testid="stVerticalBlock"] {
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        border: none !important;
    }

    /* ============================================================
       5 SEPARATE PANELS ONLY — SOLID DARK NAVY (#062B55)
       Scoped strictly via .field-ops-panel-marker.
       Compatible with both Streamlit container structures.
       ============================================================ */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker),
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) {
        background: #062B55 !important;
        background-color: #062B55 !important;
        border: 1px solid rgba(32, 196, 255, 0.45) !important;
        border-radius: 14px !important;
        padding: 24px 30px !important;
        margin: 0 auto 20px auto !important;
        max-width: 1060px !important;
        width: 100% !important;
        box-shadow: 0 8px 26px rgba(0, 0, 0, 0.45) !important;
        transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker):hover,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker):hover,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker):hover {
        border-color: rgba(32, 196, 255, 0.65) !important;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.55), 0 0 14px rgba(32, 196, 255, 0.20) !important;
    }

    /* Inner blocks / columns inside the panel stay transparent for a clean uniform solid card */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) div[data-testid="stVerticalBlock"],
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) div[data-testid="stVerticalBlock"]:not(:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker)) {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Left-Aligned Plain-Text Cyan Heading for Panels */
    .field-ops-panel-title {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #20C4FF !important;
        font-size: 1.30rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        text-align: left !important;
        margin: 0 0 1.25rem 0 !important;
        padding-bottom: 0 !important;
        border-bottom: none !important;
        width: 100% !important;
        display: block !important;
    }

    /* ALL NORMAL BODY TEXT & LABELS INSIDE FIELD OPS PANELS MUST BE WHITE (#FFFFFF) */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) label,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) label p,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) label span,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stWidgetLabel"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stWidgetLabel"] p,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stWidgetLabel"] span,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) label,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) label p,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) label span,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stWidgetLabel"],
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stWidgetLabel"] p,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stWidgetLabel"] span,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) label,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) label p,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) label span,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stWidgetLabel"],
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stWidgetLabel"] p,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stWidgetLabel"] span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        opacity: 1 !important;
    }

    /* Two-column balanced field pairs inside panels */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) div[data-testid="stHorizontalBlock"],
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) div[data-testid="stHorizontalBlock"],
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) div[data-testid="stHorizontalBlock"] {
        gap: 28px !important;
        width: 100% !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) div[data-testid="stColumn"],
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) div[data-testid="stColumn"],
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) div[data-testid="stColumn"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
        width: 100% !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) .stTextInput,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) .stSelectbox,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) .stNumberInput,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) .stTextInput,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) .stSelectbox,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) .stNumberInput,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) .stTextInput,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) .stSelectbox,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) .stNumberInput {
        width: 100% !important;
    }

    /* Text & Number Input Fields — Dark Recessed rgba(4, 20, 44, 0.95) with White Text */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) .stTextInput input,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) .stNumberInput input,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) .stTextInput input,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) .stNumberInput input,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) .stTextInput input,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) .stNumberInput input {
        background: rgba(4, 20, 44, 0.95) !important;
        background-color: rgba(4, 20, 44, 0.95) !important;
        border: 1px solid rgba(32, 196, 255, 0.35) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        padding: 10px 14px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) .stTextInput input:focus,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) .stNumberInput input:focus,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) .stTextInput input:focus,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) .stNumberInput input:focus,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) .stTextInput input:focus,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) .stNumberInput input:focus {
        border-color: #20C4FF !important;
        box-shadow: 0 0 0 2px rgba(32, 196, 255, 0.35) !important;
        outline: none !important;
    }

    /* Dropdowns (Selectbox) — Clean Continuous White Surface with #03254C Text */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] > div,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"],
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] > div {
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
        border: 1px solid rgba(32, 196, 255, 0.45) !important;
        border-radius: 8px !important;
        color: #03254C !important;
    }

    /* Ensure internal input inside selectbox has zero padding, no border, and transparent background */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] input,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] input {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 1px !important;
        min-width: 0 !important;
        max-width: 1px !important;
        outline: none !important;
    }

    /* Entire inner area including value container and arrow/icons container: transparent so it blends into white selectbox */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] div,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] span,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] [aria-hidden="true"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] [role="button"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] *::before,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] *::after,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] div,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] span,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] [aria-hidden="true"],
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] [role="button"],
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] *::before,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] *::after {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] > div:hover,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] > div:focus-within,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] > div:hover,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] > div:focus-within {
        border-color: #20C4FF !important;
        box-shadow: 0 0 0 2px rgba(32, 196, 255, 0.35) !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] span,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] span {
        color: #03254C !important;
        -webkit-text-fill-color: #03254C !important;
        font-weight: 600 !important;
    }

    /* Dropdown Arrow: dark navy #03254C cleanly visible on white selectbox */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] svg,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] svg {
        color: #03254C !important;
        fill: #03254C !important;
        stroke: #03254C !important;
        background: transparent !important;
        background-color: transparent !important;
        opacity: 1 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] svg path,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] svg path {
        fill: #03254C !important;
        stroke: #03254C !important;
        color: #03254C !important;
        opacity: 1 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] svg polyline,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] svg polyline {
        fill: none !important;
        stroke: #03254C !important;
        color: #03254C !important;
        opacity: 1 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-baseweb="select"] svg *,
    div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-baseweb="select"] svg * {
        fill: #03254C !important;
        color: #03254C !important;
    }

    /* Textarea for Details — rgba(4, 20, 44, 0.95) Background with White Text */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) textarea,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) textarea,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) textarea {
        background: rgba(4, 20, 44, 0.95) !important;
        background-color: rgba(4, 20, 44, 0.95) !important;
        border: 1px solid rgba(32, 196, 255, 0.35) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-size: 0.95rem !important;
        padding: 10px 14px !important;
        min-height: 120px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) textarea:focus,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) textarea:focus,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) textarea:focus {
        border-color: #20C4FF !important;
        box-shadow: 0 0 0 2px rgba(32, 196, 255, 0.35) !important;
        outline: none !important;
    }

    /* File Uploader for Photograph — rgba(4, 20, 44, 0.95) with Cyan dashed border */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"],
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"],
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stFileUploader"] {
        background: rgba(4, 20, 44, 0.95) !important;
        background-color: rgba(4, 20, 44, 0.95) !important;
        border: 1px dashed rgba(32, 196, 255, 0.35) !important;
        border-radius: 8px !important;
        padding: 16px !important;
        transition: border-color 0.2s ease !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"]:hover,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"]:hover,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stFileUploader"]:hover {
        border-color: #20C4FF !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] section,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] section,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stFileUploader"] section {
        background: transparent !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] span,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] small,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] p,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] span,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] small,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] p,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stFileUploader"] span,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stFileUploader"] small,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stFileUploader"] p {
        color: #FFFFFF !important;
    }

    /* Small Upload Control / Button inside Upload Photograph: White background (#FFFFFF) + Black text (#000000) */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] button,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] button *,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] button,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] button *,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stFileUploader"] button,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stFileUploader"] button *,
    .st-key-fo_photo_uploader button,
    .st-key-fo_photo_uploader button * {
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] button:hover,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] button:hover *,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] button:hover,
    .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(.field-ops-panel-marker) [data-testid="stFileUploader"] button:hover *,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stFileUploader"] button:hover,
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .field-ops-panel-marker) [data-testid="stFileUploader"] button:hover *,
    .st-key-fo_photo_uploader button:hover,
    .st-key-fo_photo_uploader button:hover * {
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* GPS Button inside Panel 4 — Centered with dark recessed background and cyan border */
    .st-key-btn_use_current_gps {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    .st-key-btn_use_current_gps button {
        background: rgba(4, 20, 44, 0.95) !important;
        background-color: rgba(4, 20, 44, 0.95) !important;
        border: 1.5px solid #20C4FF !important;
        border-radius: 20px !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 8px 24px !important;
        margin: 0 auto !important;
        display: block !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
    }
    .st-key-btn_use_current_gps button:hover {
        background-color: rgba(32, 196, 255, 0.15) !important;
        border-color: #38d8ff !important;
        box-shadow: 0 0 14px rgba(32, 196, 255, 0.4) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Submit Incident Button Container */
    .field-ops-submit-wrap {
        max-width: 1060px;
        margin: 20px auto 3.5rem auto;
        background: transparent !important;
        background-color: transparent !important;
    }
    .field-ops-submit-wrap .stButton,
    .st-key-fo_submit_btn {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    .st-key-fo_submit_btn button,
    .field-ops-submit-wrap .stButton > button {
        background: #E53935 !important;
        background-image: none !important;
        background-color: #E53935 !important;
        border: none !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border-radius: 12px !important;
        padding: 13px 28px !important;
        box-shadow: 0 4px 18px rgba(229, 57, 53, 0.45) !important;
        transition: all 0.25s ease !important;
        display: block !important;
        margin: 0 auto !important;
    }
    .st-key-fo_submit_btn button *,
    .field-ops-submit-wrap .stButton > button * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    .st-key-fo_submit_btn button:hover,
    .field-ops-submit-wrap .stButton > button:hover {
        background: #D32F2F !important;
        background-image: none !important;
        background-color: #D32F2F !important;
        box-shadow: 0 0 24px rgba(229, 57, 53, 0.70) !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    .st-key-fo_submit_btn button:hover *,
    .field-ops-submit-wrap .stButton > button:hover * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* Offline-First Field Operations Section Header: Centered horizontally */
    .fo-offline-header-wrap {
        max-width: 1060px;
        margin: 1.5rem auto 1.25rem auto;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
    }
    .fo-offline-title {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        margin: 0 0 0.35rem 0 !important;
        text-align: center !important;
        line-height: 1.3 !important;
    }
    .fo-offline-caption {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 0.875rem !important;
        font-weight: 400 !important;
        color: rgba(255, 255, 255, 0.75) !important;
        margin: 0 auto !important;
        text-align: center !important;
        line-height: 1.5 !important;
        max-width: 750px !important;
    }

    /* Field Connectivity Statistics Grid */
    .fo-stats-grid {
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important;
        gap: 16px !important;
        width: 100% !important;
        margin: 14px 0 !important;
    }
    @media (max-width: 900px) {
        .fo-stats-grid {
            grid-template-columns: repeat(2, 1fr) !important;
        }
    }
    @media (max-width: 480px) {
        .fo-stats-grid {
            grid-template-columns: 1fr !important;
        }
    }
    .fo-stat-card {
        background: rgba(4, 20, 44, 0.95) !important;
        background-color: rgba(4, 20, 44, 0.95) !important;
        border: 1px solid rgba(32, 196, 255, 0.35) !important;
        border-radius: 10px !important;
        padding: 14px 18px !important;
        display: flex !important;
        align-items: center !important;
        gap: 14px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25) !important;
        box-sizing: border-box !important;
    }
    .fo-stat-card:hover {
        border-color: #20C4FF !important;
        box-shadow: 0 0 12px rgba(32, 196, 255, 0.30) !important;
    }
    .fo-stat-icon {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-width: 32px !important;
        flex-shrink: 0 !important;
    }
    .fo-stat-content {
        display: flex !important;
        flex-direction: column !important;
    }
    .fo-stat-label {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        color: rgba(255, 255, 255, 0.70) !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        margin-bottom: 2px !important;
    }
    .fo-stat-val {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 1.55rem !important;
        font-weight: 800 !important;
        line-height: 1.1 !important;
    }

    /* Reset All button in Field Connectivity */
    .st-key-btn_reset_connectivity_stats {
        display: inline-block !important;
        width: auto !important;
        margin-top: 4px !important;
    }
    .st-key-btn_reset_connectivity_stats button {
        background: rgba(4, 20, 44, 0.95) !important;
        background-color: rgba(4, 20, 44, 0.95) !important;
        border: 1.5px solid #20C4FF !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 6px 18px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
    }
    .st-key-btn_reset_connectivity_stats button:hover {
        background-color: rgba(32, 196, 255, 0.15) !important;
        border-color: #38d8ff !important;
        box-shadow: 0 0 12px rgba(32, 196, 255, 0.40) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    @media (max-width: 768px) {
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) {
            padding: 18px 18px !important;
            margin-bottom: 16px !important;
        }
        .fo-main-title {
            font-size: 1.7rem;
        }
        .field-ops-panel-title {
            font-size: 1.15rem !important;
        }
    }

    @media (max-width: 640px) {
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.field-ops-panel-marker) div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            width: 100% !important;
        gap: 16px !important;
    }
}

    /* Green/Cyan Professional styling for Accept buttons in Public Help Requests Dispatch */
    div[class*="st-key-accept_help_"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-bottom: 10px !important;
        width: 100% !important;
    }
    div[class*="st-key-accept_help_"] button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        border: 1.5px solid #34D399 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 0.90rem !important;
        min-height: 44px !important;
        height: 44px !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        width: 100% !important;
    }
    div[class*="st-key-accept_help_"] button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        border-color: #6EE7B7 !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.55) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        transform: translateY(-1px) !important;
    }
    div[class*="st-key-accept_help_"] button:active {
        transform: translateY(1px) !important;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3) !important;
    }
    div[class*="st-key-accept_help_"] button *,
    div[class*="st-key-accept_help_"] button p,
    div[class*="st-key-accept_help_"] button span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
<div class="fo-header-container">
    <h1 class="fo-main-title">FIELD OPS</h1>
    <div class="fo-sub-description">
        Report incidents and manage field operations
    </div>
</div>
    """, unsafe_allow_html=True)
    
    # ------------------------------------------------------------
    # PANEL 1 — OFFICER INFORMATION
    # ------------------------------------------------------------
    with st.container(border=True):
        st.markdown('<div class="field-ops-panel-marker"></div><div class="field-ops-panel-title">Officer Information</div>', unsafe_allow_html=True)
        
        if st.session_state.get("user_role") != "Field Officer":
            st.warning("⚠️ **Notice**: You are browsing in **General User** mode. Incident reporting submissions require verified **Field Officer** credentials. You can switch to Field Officer from the Control Panel above or test with demo credentials below.")
        
        officer_col1, officer_col2 = st.columns(2)
        
        auth_user = st.session_state.get("authenticated_user") or get_authenticated_user()
        if auth_user and auth_user.get("role") == "Field Officer":
            default_ofc_name = auth_user.get("name", "Field Officer")
            default_ofc_id = auth_user.get("user_id", "NER-OFC-001")
        else:
            default_ofc_name = st.session_state.get("user_name", "Inspector R. K. Sharma") if st.session_state.get("user_role") == "Field Officer" else "Inspector R. K. Sharma"
            default_ofc_id = st.session_state.get("officer_id", "NER-OFC-001") if st.session_state.get("user_role") == "Field Officer" else "NER-OFC-001"
        
        with officer_col1:
            officer_name = st.text_input(
                "Officer Name",
                value=default_ofc_name,
                key="fo_officer_name"
            )
        
        with officer_col2:
            officer_id = st.text_input(
                "Officer ID",
                value=default_ofc_id,
                key="fo_officer_id"
            )
    
    # ------------------------------------------------------------
    # PANEL 2 — FIELD CONNECTIVITY
    # ------------------------------------------------------------
    if "fo_connectivity_mode" not in st.session_state or st.session_state.fo_connectivity_mode == "🟢 Online":
        st.session_state.fo_connectivity_mode = "Online"
    elif st.session_state.fo_connectivity_mode == "🔴 Offline":
        st.session_state.fo_connectivity_mode = "Offline"

    # Auto-synchronize pending reports if online mode is active
    if st.session_state.fo_connectivity_mode in ["Online", "🟢 Online"]:
        _pending_on_entry = _load_pending_reports()
        if _pending_on_entry:
            _sync_offline_reports()
            if st.session_state.get("fo_last_submission") and st.session_state.fo_last_submission.get("status") == "Pending Synchronization":
                st.session_state.fo_last_submission["status"] = "Synchronized"
                st.session_state.fo_last_submission["synced_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Read live counters directly from persistent JSON storage
    _pending_list = _load_pending_reports()
    _synced_list = _load_synced_reports()
    st.session_state.fo_pending_reports = len(_pending_list)
    st.session_state.fo_synchronized_reports = len(_synced_list)
    st.session_state.fo_total_reports = len(_pending_list) + len(_synced_list)

    with st.container(border=True):
        st.markdown('<div class="field-ops-panel-marker"></div><div class="field-ops-panel-title">📡 Field Connectivity</div>', unsafe_allow_html=True)
        
        st.markdown('<div style="font-size: 0.92rem; font-weight: 600; color: #FFFFFF; margin-bottom: 6px;">Field Connectivity Status</div>', unsafe_allow_html=True)
        
        # Radio button toggle for connectivity
        conn_choice = st.radio(
            "Field Connectivity Status",
            ["Online", "Offline"],
            index=0 if st.session_state.fo_connectivity_mode in ["Online", "🟢 Online"] else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="fo_top_conn_radio"
        )
        
        # Update connectivity state and sync pending if switching to Online
        if conn_choice != st.session_state.fo_connectivity_mode:
            st.session_state.fo_connectivity_mode = conn_choice
            if conn_choice == "Online":
                _sync_offline_reports()
                if st.session_state.get("fo_last_submission") and st.session_state.fo_last_submission.get("status") == "Pending Synchronization":
                    st.session_state.fo_last_submission["status"] = "Synchronized"
                    st.session_state.fo_last_submission["synced_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Switching back to Online: Keep GPS in manual/existing state until explicitly requested
                st.session_state.fo_gps_active = False
                st.session_state.fo_gps_error = None
            else:
                # Switching to Offline: Immediately deactivate GPS Mode
                st.session_state.fo_gps_active = False
                st.session_state.fo_gps_error = None
            
            # Recalculate counts immediately from JSON files
            st.session_state.fo_pending_reports = len(_load_pending_reports())
            st.session_state.fo_synchronized_reports = len(_load_synced_reports())
            st.session_state.fo_total_reports = st.session_state.fo_pending_reports + st.session_state.fo_synchronized_reports
            st.rerun()
        
        is_online = (st.session_state.fo_connectivity_mode in ["Online", "🟢 Online"])
        
        # Dynamic full-width status message
        if is_online:
            status_banner_html = """
            <div style="width: 100%; margin: 12px 0 16px 0; padding: 11px 18px; border-radius: 8px; background: rgba(16, 185, 129, 0.18); border: 1px solid rgba(52, 211, 153, 0.55); display: flex; align-items: center; gap: 10px;">
                <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #10B981; box-shadow: 0 0 8px #10B981; flex-shrink: 0;"></span>
                <span style="font-size: 0.92rem; font-weight: 700; color: #FFFFFF; letter-spacing: 0.02em;">
                    ONLINE MODE – Field reports can be synchronized with the central logistics system.
                </span>
            </div>
            """
        else:
            status_banner_html = """
            <div style="width: 100%; margin: 12px 0 16px 0; padding: 11px 18px; border-radius: 8px; background: rgba(239, 68, 68, 0.18); border: 1px solid rgba(248, 113, 113, 0.55); display: flex; align-items: center; gap: 10px;">
                <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #EF4444; box-shadow: 0 0 8px #EF4444; flex-shrink: 0;"></span>
                <span style="font-size: 0.92rem; font-weight: 700; color: #FFFFFF; letter-spacing: 0.02em;">
                    OFFLINE MODE – Field reports are being stored as pending records for later synchronization.
                </span>
            </div>
            """
        st.markdown(status_banner_html, unsafe_allow_html=True)
        
        # Four Statistics Cards in one row
        conn_val = "ONLINE" if is_online else "OFFLINE"
        conn_color = "#10B981" if is_online else "#EF4444"
        total_val = st.session_state.fo_total_reports
        pending_val = st.session_state.fo_pending_reports
        sync_val = st.session_state.fo_synchronized_reports
        
        cards_html = f"""
        <div class="fo-stats-grid">
            <div class="fo-stat-card">
                <div class="fo-stat-icon">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#20C4FF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a11 11 0 0 1 14.08 0"></path><path d="M1.42 9a16 16 0 0 1 21.16 0"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path><line x1="12" y1="20" x2="12.01" y2="20"></line></svg>
                </div>
                <div class="fo-stat-content">
                    <div class="fo-stat-label">CONNECTIVITY</div>
                    <div class="fo-stat-val" style="color: {conn_color};">{conn_val}</div>
                </div>
            </div>
            <div class="fo-stat-card">
                <div class="fo-stat-icon">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#20C4FF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                </div>
                <div class="fo-stat-content">
                    <div class="fo-stat-label">TOTAL REPORTS</div>
                    <div class="fo-stat-val" style="color: #FFFFFF;">{total_val}</div>
                </div>
            </div>
            <div class="fo-stat-card">
                <div class="fo-stat-icon">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                </div>
                <div class="fo-stat-content">
                    <div class="fo-stat-label">PENDING</div>
                    <div class="fo-stat-val" style="color: #F59E0B;">{pending_val}</div>
                </div>
            </div>
            <div class="fo-stat-card">
                <div class="fo-stat-icon">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#20C4FF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                </div>
                <div class="fo-stat-content">
                    <div class="fo-stat-label">SYNCHRONIZED</div>
                    <div class="fo-stat-val" style="color: #20C4FF;">{sync_val}</div>
                </div>
            </div>
        </div>
        """
        st.markdown(cards_html, unsafe_allow_html=True)
        
        # Reset All Button
        if st.button("↻ Reset All", key="btn_reset_connectivity_stats"):
            _save_pending_reports([])
            _save_synced_reports([])
            st.session_state.fo_total_reports = 0
            st.session_state.fo_pending_reports = 0
            st.session_state.fo_synchronized_reports = 0
            st.session_state.fo_last_submission = None
            st.session_state.offline_reports = []
            st.session_state.submitted_reports = []
            if "fo_details_input" in st.session_state:
                st.session_state.fo_details_input = ""
            if "fo_other_incident" in st.session_state:
                st.session_state.fo_other_incident = ""
            if "fo_gps_error" in st.session_state:
                st.session_state.fo_gps_error = None
            st.rerun()
    
    # ------------------------------------------------------------
    # PANEL 3 — INCIDENT INFORMATION
    # ------------------------------------------------------------
    with st.container(border=True):
        st.markdown('<div class="field-ops-panel-marker"></div><div class="field-ops-panel-title">Incident Information</div>', unsafe_allow_html=True)
        
        incident_col1, incident_col2 = st.columns(2)
        
        with incident_col1:
            incident_type = st.selectbox(
                "Incident Type",
                [
                    "Road Blockage",
                    "Infrastructure Damage",
                    "Vehicle Breakdown",
                    "Accident",
                    "Flooding",
                    "Landslide",
                    "Other"
                ],
                index=0,
                key="fo_incident_type"
            )
        
        with incident_col2:
            severity = st.selectbox(
                "Severity",
                [
                    "Low",
                    "Medium",
                    "High",
                    "Critical"
                ],
                index=0,
                key="fo_severity"
            )
        
        other_incident = ""
        if incident_type in ["Other", "Others"]:
            other_incident = st.text_input(
                "Describe Other Incident",
                placeholder="Enter the incident not covered above...",
                key="fo_other_incident"
            )
    
    # ------------------------------------------------------------
    # PANEL 3 — AFFECTED LOCATION
    # ------------------------------------------------------------
    with st.container(border=True):
        st.markdown('<div class="field-ops-panel-marker"></div><div class="field-ops-panel-title">Affected Location</div>', unsafe_allow_html=True)
        
        location_col1, location_col2 = st.columns(2)
        
        with location_col1:
            district = st.selectbox(
                "District",
                [
                    "Imphal",
                    "Shillong",
                    "Aizawl",
                    "Agartala",
                    "Guwahati"
                ],
                index=0,
                key="fo_district"
            )
        
        with location_col2:
            corridor = st.selectbox(
                "Affected Corridor",
                [
                    "Corridor A",
                    "Corridor B",
                    "Corridor C"
                ],
                index=0,
                key="fo_corridor"
            )
    
    # ------------------------------------------------------------
    # PANEL 4 — CURRENT GPS LOCATION
    # ------------------------------------------------------------
    is_online = (st.session_state.fo_connectivity_mode in ["Online", "🟢 Online"])
    
    if "fo_gps_active" not in st.session_state:
        st.session_state.fo_gps_active = False
    elif not is_online:
        st.session_state.fo_gps_active = False

    if "fo_gps_trigger_id" not in st.session_state:
        st.session_state.fo_gps_trigger_id = 0
    if "fo_lat_input" not in st.session_state:
        st.session_state.fo_lat_input = 24.817000
    if "fo_lon_input" not in st.session_state:
        st.session_state.fo_lon_input = 93.936800
    if "fo_gps_error" not in st.session_state:
        st.session_state.fo_gps_error = None
    if "fo_gps_accuracy" not in st.session_state:
        st.session_state.fo_gps_accuracy = None

    with st.container(border=True):
        st.markdown('<div class="field-ops-panel-marker"></div><div class="field-ops-panel-title">Current GPS Location</div>', unsafe_allow_html=True)
        
        # Centered GPS Button
        gps_btn_col1, gps_btn_col2, gps_btn_col3 = st.columns([1, 1.6, 1])
        with gps_btn_col2:
            use_gps_clicked = st.button(
                "📍 Use Current GPS Location",
                key="btn_use_current_gps",
                use_container_width=True
            )
            if use_gps_clicked:
                if not is_online:
                    st.session_state.fo_gps_active = False
                    st.session_state.fo_gps_error = "GPS is unavailable in Offline Mode. Switch Field Connectivity to Online to enable live GPS."
                else:
                    st.session_state.fo_gps_active = True
                    st.session_state.fo_gps_trigger_id = st.session_state.get("fo_gps_trigger_id", 0) + 1
                    st.session_state.fo_gps_error = None

        # Execute real-time browser geolocation component (active only when online)
        gps_result = _realtime_gps_tracker(
            active=is_online and st.session_state.get("fo_gps_active", False),
            triggerId=st.session_state.fo_gps_trigger_id if is_online else 0,
            isOnline=is_online,
            key="fo_browser_gps_component"
        )

        if is_online and st.session_state.get("fo_gps_active", False) and gps_result and isinstance(gps_result, dict):
            if gps_result.get("error"):
                st.session_state.fo_gps_error = gps_result["error"]
            elif gps_result.get("lat") is not None and gps_result.get("lon") is not None:
                new_lat = round(float(gps_result["lat"]), 6)
                new_lon = round(float(gps_result["lon"]), 6)
                st.session_state.fo_lat_input = new_lat
                st.session_state.fo_lon_input = new_lon
                st.session_state.fo_gps_accuracy = gps_result.get("accuracy")
                st.session_state.fo_gps_error = None

        is_gps_active = is_online and st.session_state.get("fo_gps_active", False)
        
        # Centered GPS status badge
        if is_online and is_gps_active:
            status_html = """
            <div style="text-align: center; margin: 12px 0 18px 0;">
                <span style="display: inline-flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.20); border: 1px solid rgba(52, 211, 153, 0.55); color: #FFFFFF; padding: 6px 20px; border-radius: 999px; font-weight: 700; font-size: 0.85rem; letter-spacing: 0.04em;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981;"></span>
                    GPS Mode: ACTIVE
                </span>
            </div>
            """
        elif not is_online:
            status_html = """
            <div style="text-align: center; margin: 12px 0 18px 0;">
                <span style="display: inline-flex; align-items: center; gap: 8px; background: rgba(239, 68, 68, 0.20); border: 1px solid rgba(248, 113, 113, 0.55); color: #FFFFFF; padding: 6px 20px; border-radius: 999px; font-weight: 700; font-size: 0.85rem; letter-spacing: 0.04em;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #ef4444; box-shadow: 0 0 8px #ef4444;"></span>
                    GPS Mode: DISABLED (OFFLINE)
                </span>
            </div>
            """
        else:
            status_html = """
            <div style="text-align: center; margin: 12px 0 18px 0;">
                <span style="display: inline-flex; align-items: center; gap: 8px; background: rgba(245, 158, 11, 0.20); border: 1px solid rgba(245, 158, 11, 0.45); color: #FFFFFF; padding: 6px 20px; border-radius: 999px; font-weight: 700; font-size: 0.85rem; letter-spacing: 0.04em;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #f59e0b;"></span>
                    GPS Mode: MANUAL OVERRIDE
                </span>
            </div>
            """
        st.markdown(status_html, unsafe_allow_html=True)

        # GPS Error banner if any
        if st.session_state.get("fo_gps_error"):
            st.markdown(f"""
            <div style="text-align: center; margin: 0 0 16px 0;">
                <span style="display: inline-flex; align-items: center; gap: 6px; background: rgba(239, 68, 68, 0.18); border: 1px solid rgba(239, 68, 68, 0.45); color: #FCA5A5; padding: 6px 18px; border-radius: 8px; font-size: 0.84rem; font-weight: 600;">
                    ⚠️ {st.session_state.fo_gps_error}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # Two columns: Latitude and Longitude
        coord_col1, coord_col2 = st.columns(2)
        with coord_col1:
            latitude = st.number_input(
                "Latitude",
                format="%.6f",
                step=0.000100,
                key="fo_lat_input"
            )
        
        with coord_col2:
            longitude = st.number_input(
                "Longitude",
                format="%.6f",
                step=0.000100,
                key="fo_lon_input"
            )

        # Synchronize coordinates into session state
        st.session_state.fo_current_lat = latitude
        st.session_state.fo_current_lon = longitude
        
        # Centered GPS Fix text (WHITE text)
        if not is_online:
            fix_text = "GPS Fix: Unavailable (Offline — Manual Coordinates Entry)"
        elif st.session_state.get("fo_gps_accuracy") is not None and is_gps_active:
            fix_text = f"GPS Fix: Live Real-Time Browser GPS Fix (Accuracy: ±{st.session_state.fo_gps_accuracy:.1f}m)"
        else:
            fix_text = "GPS Fix: Standard Station GPS Fix"

        st.markdown(f"""
        <div style="text-align: center; margin-top: 14px; font-size: 0.90rem; color: #FFFFFF; font-weight: 500;">
            {fix_text}
        </div>
        """, unsafe_allow_html=True)
    
    # ------------------------------------------------------------
    # PANEL 5 — DETAILS & PHOTOGRAPH
    # ------------------------------------------------------------
    with st.container(border=True):
        st.markdown('<div class="field-ops-panel-marker"></div><div class="field-ops-panel-title">Details & Photograph</div>', unsafe_allow_html=True)
        
        description = st.text_area(
            "Incident Details",
            placeholder="Enter detailed incident information...",
            height=120,
            key="fo_details_input"
        )
        
        st.markdown('<div style="margin-top: 16px; margin-bottom: 8px; font-weight: 600; color: #FFFFFF; font-size: 0.95rem;">Upload Photograph</div>', unsafe_allow_html=True)
        
        uploaded_image = st.file_uploader(
            "Select geo-tagged incident photograph",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
            key="fo_photo_uploader"
        )
        
        if uploaded_image is not None:
            filename = uploaded_image.name
            st.markdown(f"""
            <div class="field-ops-photo-preview-box" style="margin-top: 10px; padding: 12px; background: rgba(4, 20, 44, 0.95); border: 1px solid rgba(32, 196, 255, 0.35); border-radius: 8px; text-align: center;">
                <div style="font-size: 0.88rem; color: #FFFFFF; font-weight: 600; margin-bottom: 8px;">
                    📎 Attached File: <span style="color: #20C4FF;">{filename}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.image(
                uploaded_image,
                caption=f"Incident Photograph: {filename}",
                use_container_width=True
            )
            st.success("✅ Photograph attached successfully.")
        else:
            st.markdown("""
            <div style="margin-top: 8px; padding: 10px 14px; background: rgba(4, 20, 44, 0.95); border: 1px dashed rgba(32, 196, 255, 0.35); border-radius: 8px; color: #FFFFFF; font-size: 0.88rem; text-align: center;">
                📷 No photograph uploaded
            </div>
            """, unsafe_allow_html=True)
    
    # ------------------------------------------------------------
    # SUBMIT INCIDENT REPORT (Centered below 5 panels)
    # ------------------------------------------------------------
    st.markdown('<div class="field-ops-submit-wrap">', unsafe_allow_html=True)
    sub_col1, sub_col2, sub_col3 = st.columns([1.15, 1.55, 1.15])
    with sub_col2:
        submit_incident = st.button(
            "Submit Incident Report",
            use_container_width=True,
            key="fo_submit_btn"
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if submit_incident:
        if not officer_name.strip():
            st.error("Please enter the officer name.")
            st.session_state.fo_last_submission = None
        elif incident_type in ["Other", "Others"] and not other_incident.strip():
            st.error("Please describe the other incident.")
            st.session_state.fo_last_submission = None
        else:
            created_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            unique_suffix = int(time.time() * 1000) % 1000000

            if not is_online:
                # OFFLINE MODE — STORE LOCALLY IN PENDING QUEUE
                current_pending = _load_pending_reports()
                
                # Check maximum limit of 5 pending offline reports
                if len(current_pending) >= 5:
                    st.error("Offline pending limit reached (5 reports). Reconnect to synchronize before submitting another report.")
                    st.session_state.fo_last_submission = None
                else:
                    report_id = f"NER-OFF-{unique_suffix:06d}"
                    existing_ids = {r.get("report_id") for r in current_pending} | {r.get("report_id") for r in _load_synced_reports()}
                    while report_id in existing_ids:
                        unique_suffix = (unique_suffix + 1) % 1000000
                        report_id = f"NER-OFF-{unique_suffix:06d}"
                    
                    report_data = {
                        "report_id": report_id,
                        "officer_name": officer_name.strip(),
                        "officer_id": officer_id.strip(),
                        "incident_type": incident_type,
                        "other_incident": other_incident.strip() if incident_type in ["Other", "Others"] else "",
                        "severity": severity,
                        "district": district,
                        "corridor": corridor,
                        "location": f"{district}, {corridor}",
                        "latitude": round(float(latitude), 6),
                        "longitude": round(float(longitude), 6),
                        "details": description.strip(),
                        "photo_filename": uploaded_image.name if uploaded_image is not None else None,
                        "timestamp": created_ts,
                        "status": "Pending Synchronization",
                        "synced_at": None
                    }
                    
                    current_pending.append(report_data)
                    _save_pending_reports(current_pending)
                    
                    st.session_state.fo_last_submission = report_data
                    st.rerun()
            else:
                # ONLINE MODE — STORE IN SYNCHRONIZED STORAGE
                report_id = f"NER-ONL-{unique_suffix:06d}"
                current_synced = _load_synced_reports()
                existing_ids = {r.get("report_id") for r in current_synced} | {r.get("report_id") for r in _load_pending_reports()}
                while report_id in existing_ids:
                    unique_suffix = (unique_suffix + 1) % 1000000
                    report_id = f"NER-ONL-{unique_suffix:06d}"
                
                report_data = {
                    "report_id": report_id,
                    "officer_name": officer_name.strip(),
                    "officer_id": officer_id.strip(),
                    "incident_type": incident_type,
                    "other_incident": other_incident.strip() if incident_type in ["Other", "Others"] else "",
                    "severity": severity,
                    "district": district,
                    "corridor": corridor,
                    "location": f"{district}, {corridor}",
                    "latitude": round(float(latitude), 6),
                    "longitude": round(float(longitude), 6),
                    "details": description.strip(),
                    "photo_filename": uploaded_image.name if uploaded_image is not None else None,
                    "timestamp": created_ts,
                    "status": "Synchronized",
                    "synced_at": created_ts
                }
                
                current_synced.append(report_data)
                _save_synced_reports(current_synced)
                
                st.session_state.fo_last_submission = report_data
                st.rerun()

    if st.session_state.get("fo_last_submission"):
        sub_info = st.session_state.fo_last_submission
        is_sub_pending = (sub_info.get("status") == "Pending Synchronization")
        
        if is_sub_pending:
            st.warning(f"💾 Report {sub_info['report_id']} saved locally — PENDING / Awaiting Synchronization until connectivity is restored.")
        else:
            st.success(f"✅ Incident report {sub_info['report_id']} submitted successfully.")
            
        with st.container(border=True):
            if is_sub_pending:
                st.markdown('<div class="field-ops-panel-marker"></div><div class="field-ops-panel-title">Submitted Incident Summary (Stored Locally)</div>', unsafe_allow_html=True)
                st.markdown("""
                <div style="margin-bottom: 14px;">
                    <span style="display: inline-flex; align-items: center; gap: 8px; background: rgba(245, 158, 11, 0.20); border: 1px solid rgba(245, 158, 11, 0.55); color: #F59E0B; padding: 6px 16px; border-radius: 999px; font-weight: 700; font-size: 0.85rem; letter-spacing: 0.03em;">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background: #F59E0B; box-shadow: 0 0 8px #F59E0B;"></span>
                        STATUS: PENDING / AWAITING SYNCHRONIZATION
                    </span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="field-ops-panel-marker"></div><div class="field-ops-panel-title">Submitted Incident Summary</div>', unsafe_allow_html=True)
                st.markdown("""
                <div style="margin-bottom: 14px;">
                    <span style="display: inline-flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.20); border: 1px solid rgba(52, 211, 153, 0.55); color: #10B981; padding: 6px 16px; border-radius: 999px; font-weight: 700; font-size: 0.85rem; letter-spacing: 0.03em;">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background: #10B981; box-shadow: 0 0 8px #10B981;"></span>
                        STATUS: SYNCHRONIZED
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            submitted_col1, submitted_col2 = st.columns(2)
            with submitted_col1:
                st.markdown(f"<div style='color:#FFFFFF; margin-bottom:4px;'><b>Report ID:</b> <span style='color:#20C4FF;'>{sub_info['report_id']}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color:#FFFFFF; margin-bottom:4px;'><b>Timestamp:</b> {sub_info.get('timestamp', '')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color:#FFFFFF; margin-bottom:4px;'><b>Officer:</b> {sub_info.get('officer_name', '')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color:#FFFFFF; margin-bottom:4px;'><b>Officer ID:</b> {sub_info.get('officer_id', '')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color:#FFFFFF; margin-bottom:4px;'><b>Incident:</b> {sub_info.get('incident_type', '')}</div>", unsafe_allow_html=True)
                if sub_info.get("other_incident"):
                    st.markdown(f"<div style='color:#FFFFFF; margin-bottom:4px;'><b>Other Incident:</b> {sub_info['other_incident']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color:#FFFFFF; margin-bottom:4px;'><b>Severity:</b> {sub_info.get('severity', '')}</div>", unsafe_allow_html=True)
            with submitted_col2:
                st.markdown(f"<div style='color:#FFFFFF; margin-bottom:4px;'><b>District:</b> {sub_info.get('district', '')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color:#FFFFFF; margin-bottom:4px;'><b>Corridor:</b> {sub_info.get('corridor', '')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color:#FFFFFF; margin-bottom:4px;'><b>Latitude:</b> {sub_info.get('latitude', 0.0):.6f}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color:#FFFFFF; margin-bottom:4px;'><b>Longitude:</b> {sub_info.get('longitude', 0.0):.6f}</div>", unsafe_allow_html=True)
                if sub_info.get("photo_filename"):
                    st.markdown(f"<div style='color:#FFFFFF; margin-bottom:4px;'><b>Photograph:</b> {sub_info['photo_filename']}{' (Stored offline)' if is_sub_pending else ''}</div>", unsafe_allow_html=True)
            
            if sub_info.get("details"):
                st.markdown(f"<div style='margin-top:10px; color:#FFFFFF;'><b>Details:</b> {sub_info['details']}</div>", unsafe_allow_html=True)
            
            if is_sub_pending:
                pending_now = len(_load_pending_reports())
                st.info(f"💾 Report stored in offline pending queue ({pending_now} of 5 max). Automatic synchronization will occur when network connectivity is restored.")
            else:
                st.info("📡 Incident received by the central logistics intelligence system.")
            
            if sub_info.get("severity") == "Critical":
                st.error("🔴 CRITICAL INCIDENT — Immediate operational review recommended.")
            elif sub_info.get("severity") == "High":
                st.warning("🟠 HIGH-SEVERITY INCIDENT — Monitor affected corridor and evaluate alternate routing.")
            else:
                st.info("🟢 Incident recorded for monitoring.")
        
    # ============================================================
    # PART 9 — OFFLINE-FIRST FIELD OPERATIONS
    # ============================================================
    
    st.markdown("---")
    
    # ------------------------------------------------------------
    # Initialize offline report storage
    # ------------------------------------------------------------
    
    if "offline_reports" not in st.session_state:
    
        st.session_state.offline_reports = []
    
    # ------------------------------------------------------------
    # Network status & sync tracking (internal state)
    # ------------------------------------------------------------
    network_status = st.session_state.get("fo_connectivity_mode", "Online")
    pending_reports = sum(
        1
        for report in st.session_state.offline_reports
        if report["status"] == "Pending Synchronization"
    )
    

    # ---------------------------------------------------------
    # PANEL 6 — OPERATIONAL MAP & CORRIDOR ACCESSIBILITY
    # ---------------------------------------------------------
    with st.container(border=True):
        st.markdown('<div class="field-ops-panel-marker"></div><div class="field-ops-panel-title">Operational Map & Corridor Accessibility</div>', unsafe_allow_html=True)
        
        # CREATE NER MAP WITH BASE TILES (Zoom controls and Leaflet attribution preserved)
        ner_map = folium.Map(
            location=[25.8, 93.9],
            zoom_start=6,
            tiles="OpenStreetMap"
        )
        
        # REPRESENTATIVE ROAD NETWORK (Borders, Roads, Labels preserved)
        roads = [
            {
                "name": "Corridor A",
                "points": [
                    [26.14, 91.74],
                    [25.57, 91.88],
                    [24.82, 93.94]
                ],
                "status": "blocked"
            },
            {
                "name": "Corridor B",
                "points": [
                    [26.14, 91.74],
                    [25.67, 94.11],
                    [25.57, 93.72]
                ],
                "status": "safe"
            },
            {
                "name": "Corridor C",
                "points": [
                    [25.57, 93.72],
                    [24.82, 93.94],
                    [24.75, 94.03]
                ],
                "status": "risk"
            },
            {
                "name": "Corridor D",
                "points": [
                    [25.57, 93.72],
                    [26.20, 92.94],
                    [26.75, 94.20]
                ],
                "status": "safe"
            }
        ]
        
        # DRAW ROADS
        for road in roads:
            if road["status"] == "blocked":
                road_color = "red"
                road_weight = 7
            elif road["status"] == "risk":
                road_color = "orange"
                road_weight = 6
            else:
                road_color = "green"
                road_weight = 5
        
            folium.PolyLine(
                locations=road["points"],
                color=road_color,
                weight=road_weight,
                opacity=0.8,
                tooltip=f"{road['name']} — {road['status'].upper()}"
            ).add_to(ner_map)

        # ADD PUBLIC USER HELP REQUESTS AS OPERATIONAL MAP MARKERS
        for h_req in _load_public_help_requests():
            if h_req.get("status", "").upper() == "ACCEPTED" or h_req.get("handled"):
                continue  # Filter accepted requests from active emergency pins
            h_lat = h_req.get("latitude")
            h_lon = h_req.get("longitude")
            if h_lat and h_lon:
                folium.Marker(
                    location=[float(h_lat), float(h_lon)],
                    popup=f"<b>🆘 {h_req.get('help_request_id')}</b><br><b>Status:</b> {h_req.get('status', 'New')}<br><b>Time:</b> {h_req.get('timestamp')}<br><b>Details:</b> {h_req.get('description', '')}",
                    tooltip=f"🆘 Public Help: {h_req.get('help_request_id')}",
                    icon=folium.Icon(color="red", icon="exclamation-sign")
                ).add_to(ner_map)

        # ADD INTERACTIVE POINTER / ERASER TOOL
        ner_map.add_child(LeafletInteractiveMapTools())

        # EMBED MAP INSIDE PANEL (Bounded strictly to panel width, matching other panels)
        components.html(
            ner_map.get_root().render(),
            height=580,
            scrolling=False
        )

        st.markdown("""
        <div style="display:flex; justify-content:center; align-items:center; flex-wrap:wrap; gap:24px; margin-top:10px; font-size:0.86rem; color:#FFFFFF; font-weight:600;">
            <span style="display:inline-flex; align-items:center; gap:6px;">
                <span style="color:#10B981; font-size:1.1rem;">●</span> Corridor Safe / Accessible
            </span>
            <span style="display:inline-flex; align-items:center; gap:6px;">
                <span style="color:#F59E0B; font-size:1.1rem;">●</span> Corridor At-Risk (Advisory)
            </span>
            <span style="display:inline-flex; align-items:center; gap:6px;">
                <span style="color:#EF4444; font-size:1.1rem;">●</span> Corridor Road Blockage / Closed
            </span>
        </div>
        """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # PANEL 7 — PUBLIC TRANSPORTER HELP REQUESTS DISPATCH
    # ---------------------------------------------------------
    pub_requests = _load_public_help_requests()
    active_requests = [
        r for r in pub_requests 
        if r.get("status", "").upper() != "ACCEPTED" and not r.get("handled")
    ]
    with st.container(border=True):
        st.markdown('<div class="field-ops-panel-marker"></div><div class="field-ops-panel-title">🆘 Public Transporter Help Requests (Live Field Dispatch)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="margin-bottom: 12px; font-size: 0.85rem; color: #94a3b8;">
            Live incoming distress and route assistance transmissions from commercial transporters and public motorists.
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.get("pub_help_accepted_msg"):
            st.success(st.session_state["pub_help_accepted_msg"])
            st.session_state["pub_help_accepted_msg"] = None

        if not active_requests:
            st.markdown("""
            <div style="background: rgba(15, 23, 42, 0.6); border: 1px dashed rgba(56, 189, 248, 0.25); border-radius: 10px; padding: 16px; text-align: center; color: #94a3b8; font-size: 0.85rem;">
                ✅ All incoming transporter help requests have been acknowledged and dispatched. No active requests pending.
            </div>
            """, unsafe_allow_html=True)
        else:
            auth_u = st.session_state.get("authenticated_user") or get_authenticated_user() or {}
            ofc_name = auth_u.get("name") or st.session_state.get("user_name", "Field Officer")
            ofc_id = auth_u.get("user_id") or st.session_state.get("officer_id", "FO-DISPATCH")

            for req in active_requests:
                req_id = req.get("help_request_id", "REQ-HELP")
                req_time = req.get("timestamp", "")
                req_lat = req.get("latitude", 0.0)
                req_lon = req.get("longitude", 0.0)
                req_desc = req.get("description", "")
                req_status = req.get("status", "New")
                requester = req.get("requester", {})
                req_by = requester.get("name", "Public Transporter")
                req_org = requester.get("organization", "NorthEast Freight")
                
                col_card, col_act = st.columns([5.2, 1.0], vertical_alignment="center")
                with col_card:
                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 12px; padding: 14px 18px; margin-bottom: 10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:6px;">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span style="font-size:1.1rem;">🆘</span>
                                <span style="font-family:'Outfit',sans-serif; font-weight:800; color:#38bdf8; font-size:0.95rem;">{req_id}</span>
                                <span style="display:inline-block; font-size:0.70rem; background:rgba(239, 68, 68, 0.2); color:#fca5a5; padding:2px 8px; border-radius:4px; font-weight:700; border:1px solid rgba(239,68,68,0.35);">
                                    PUBLIC HELP REQUEST
                                </span>
                            </div>
                            <div style="display:flex; align-items:center; gap:10px;">
                                <span style="display:inline-block; font-size:0.72rem; background:rgba(16, 185, 129, 0.15); color:#34d399; padding:2px 8px; border-radius:4px; font-weight:700;">
                                    STATUS: {req_status.upper()}
                                </span>
                                <span style="font-size:0.78rem; color:#94a3b8;">🕒 {req_time}</span>
                            </div>
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:8px; font-size:0.82rem; color:#ffffff; margin-bottom:6px;">
                            <div><b>Requester:</b> <span style="color:#cbd5e1;">{req_by} ({req_org})</span></div>
                            <div><b>Coordinates:</b> <span style="color:#38bdf8;">{req_lat:.6f}°N, {req_lon:.6f}°E</span></div>
                        </div>
                        <div style="font-size:0.84rem; color:#f1f5f9; background:rgba(0,0,0,0.25); padding:8px 12px; border-radius:8px; border:1px solid rgba(255,255,255,0.05); margin-top:4px;">
                            <b>Description:</b> {req_desc}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_act:
                    if st.button("✓ Accept", key=f"accept_help_{req_id}", use_container_width=True, help=f"Accept and dispatch units for Help Request {req_id}"):
                        _accept_public_help_request(req_id, officer_name=ofc_name, officer_id=ofc_id)
                        st.session_state["pub_help_accepted_msg"] = f"✅ Dispatched unit & accepted Help Request {req_id}"
                        st.rerun()


    
    # ---------------------------------------------------------


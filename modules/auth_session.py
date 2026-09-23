import os
import json
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SESSION_FILE = os.path.join(DATA_DIR, "active_session.json")

def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def save_active_session(user_data):
    """
    Saves the authenticated user dictionary to persistent storage
    and initializes central session state variables.
    """
    if not user_data:
        return
    _ensure_data_dir()
    
    # Store complete identity in st.session_state.authenticated_user as required
    role = user_data.get("role", "Field Officer")
    st.session_state.authenticated_user = {
        "name": user_data.get("name", "Field Officer"),
        "role": role,
        "access_profile": user_data.get("access_profile") or role,
        "user_id": user_data.get("user_id", "NER-OFC-001"),
        "email": user_data.get("email", ""),
        "department": user_data.get("department", "Assam Highway Command & BRO"),
        "organization": user_data.get("organization", "NorthEast Express Logistics"),
        "authenticated": True
    }
    
    # Keep flat session state keys synchronized
    st.session_state.authenticated = True
    st.session_state.user_name = st.session_state.authenticated_user["name"]
    st.session_state.user_role = st.session_state.authenticated_user["role"]
    st.session_state.access_profile = st.session_state.authenticated_user["access_profile"]
    st.session_state.officer_id = st.session_state.authenticated_user["user_id"]
    st.session_state.department = st.session_state.authenticated_user["department"]
    st.session_state.organization = st.session_state.authenticated_user["organization"]

    # Persist to JSON file
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.authenticated_user, f, indent=2)
    except Exception as e:
        print(f"[AUTH_SESSION] Error saving active session: {e}")

def load_active_session():
    """
    Reads active session from persistent storage and reconnects session state.
    Returns user dict if active, None otherwise.
    """
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data.get("authenticated"):
            # Restore to session state
            st.session_state.authenticated_user = data
            st.session_state.authenticated = True
            st.session_state.user_name = data.get("name", "Field Officer")
            st.session_state.user_role = data.get("role", "Field Officer")
            st.session_state.access_profile = data.get("access_profile", data.get("role", "Field Officer"))
            st.session_state.officer_id = data.get("user_id", "NER-OFC-001")
            st.session_state.department = data.get("department", "Assam Highway Command & BRO")
            st.session_state.organization = data.get("organization", "NorthEast Express Logistics")
            return data
    except Exception as e:
        print(f"[AUTH_SESSION] Error loading active session: {e}")
    return None

def clear_active_session():
    """
    Clears authenticated user identity on logout.
    """
    st.session_state.authenticated = False
    st.session_state.authenticated_user = None
    st.session_state.user_name = None
    st.session_state.user_role = None
    st.session_state.officer_id = None
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
        except Exception as e:
            print(f"[AUTH_SESSION] Error removing session file: {e}")

def get_authenticated_user():
    """
    Single source of truth for the logged-in user profile.
    Checks session state, then falls back to persistent storage.
    """
    user = st.session_state.get("authenticated_user")
    if user and isinstance(user, dict) and user.get("authenticated"):
        return user
    return load_active_session()

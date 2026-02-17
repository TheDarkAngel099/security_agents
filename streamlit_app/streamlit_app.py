import streamlit as st
import requests

# Set page config
st.set_page_config(page_title="Security Agent Portal", page_icon="🛡️", layout="wide")

import os

# API Config
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

def init_session_state():
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "role" not in st.session_state:
        st.session_state.role = None

init_session_state()

def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.role = None
    st.rerun()

# ─── NAVIGATION ─────────────────────────────────────────────────────────────

if not st.session_state.user:
    # Show Login View
    from views import login
    login.show(API_URL)
else:
    # Sidebar
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.user}")
        st.caption(f"Role: {st.session_state.role}")
        st.divider()
        
        if st.button("Logout", type="primary"):
            logout()

    # Routing based on Role
    role = st.session_state.role
    
    if role == "employee":
        from views import employee
        employee.show(API_URL)
        
    elif role == "hr":
        from views import hr
        hr.show(API_URL)
        
    elif role == "security":
        from views import security
        security.show(API_URL)
        
    elif role == "admin":
        # Admin can switch views for demo purposes or see dashboard
        view = st.sidebar.radio("Navigate", ["Admin Dashboard", "All Incidents (HR View)", "All Incidents (Security View)"])
        
        if view == "Admin Dashboard":
            from views import admin
            admin.show(API_URL)
        elif view == "All Incidents (HR View)":
            from views import hr
            hr.show(API_URL)
        elif view == "All Incidents (Security View)":
            from views import security
            security.show(API_URL)
    
    else:
        st.error("Unknown role.")

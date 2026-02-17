import streamlit as st
import requests
import pandas as pd
import time

def show(api_url):
    st.markdown("## 🛠️ System Admin Dashboard")
    
    # Auto-refresh logic (basic)
    if st.button("Refresh Data"):
        st.rerun()

    col1, col2, col3, col4 = st.columns(4)
    
    try:
        stats = requests.get(f"{api_url}/dashboard/stats").json()
        col1.metric("Total Incidents", stats["total_incidents"])
        col2.metric("HR Pending", stats["hr_pending"])
        col3.metric("Security Pending", stats["security_pending"])
        col4.metric("Resolved", stats["resolved"])
    except:
        st.error("Stats unavailable")

    st.divider()
    
    st.subheader("System Logs")
    try:
        logs = requests.get(f"{api_url}/dashboard/logs").json()
        if logs:
            df = pd.DataFrame(logs)
            st.dataframe(df[["timestamp", "agent", "message"]].style.applymap(lambda x: 'background-color: #222222', subset=['agent']))
        else:
            st.info("No logs available")
    except Exception as e:
        st.error(f"Failed to fetch logs: {e}")

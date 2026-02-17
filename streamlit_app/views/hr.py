import streamlit as st
import requests
import pandas as pd

def show(api_url):
    st.markdown("## 👥 HR Compliance Dashboard")
    
    # Fetch Incidents
    try:
        resp = requests.get(f"{api_url}/dashboard/incidents", params={"role": "HR"})
        incidents = resp.json()
    except Exception as e:
        st.error(f"Failed to fetch incidents: {e}")
        return

    if not incidents:
        st.info("No HR incidents found.")
        return

    # Tabs for Status
    tab1, tab2 = st.tabs(["Pending", "Resolved"])
    
    with tab1:
        pending = [i for i in incidents if i["status"] == "Pending"]
        if not pending:
            st.success("No pending incidents.")
        else:
            for inc in pending:
                with st.expander(f"{inc['risk_level']} Risk - {inc['violation_type']} (ID: {inc['id']})"):
                    st.write(f"**Sender:** {inc['sender']} -> **Recipient:** {inc['recipient']}")
                    st.text_area("Original Message", inc['original_text'], disabled=True)
                    st.write(f"**Details:** {inc['violation_details']}")
                    
                    if st.button("Resolve Incident", key=f"res_{inc['id']}"):
                         requests.patch(f"{api_url}/dashboard/incidents/{inc['id']}", json={
                             "status": "Resolved",
                             "resolution_notes": f"Resolved via Streamlit by {st.session_state.user}"
                         })
                         st.rerun()

    with tab2:
        resolved = [i for i in incidents if i["status"] == "Resolved"]
        if resolved:
            df = pd.DataFrame(resolved)
            st.dataframe(df[["id", "sender", "violation_type", "resolution_notes", "created_at"]])

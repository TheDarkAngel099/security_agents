import streamlit as st
import requests

def show(api_url):
    st.markdown("## 💬 Employee Chat - Security Assisted")
    st.info("Your messages are scanned by our AI Safety Agent before sending.")

    # Initialize State
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "draft_text" not in st.session_state:
        st.session_state.draft_text = ""
        
    if "scan_result" not in st.session_state:
        st.session_state.scan_result = None

    # Recipient Input
    recipient = st.text_input("Recipient", value="team@company.com")

    # Message Input
    draft = st.text_area("Message Draft", height=150, key="draft_input")
    
    col1, col2 = st.columns([1, 5])
    
    with col1:
        if st.button("Scan & Send", type="primary"):
            if draft:
                with st.spinner("Scanning..."):
                    try:
                        resp = requests.post(f"{api_url}/workflow/scan", json={
                            "text": draft,
                            "sender": st.session_state.user,
                            "recipient": recipient
                        })
                        if resp.status_code == 200:
                            st.session_state.scan_result = resp.json()
                        else:
                            st.error("Scan failed.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # Handle Scan Result
    if st.session_state.scan_result:
        result = st.session_state.scan_result
        
        if not result["violation_detected"]:
             st.success("✅ Good to go! Message sent successfully.")
             # In a real app, we would clear the draft here
             st.session_state.scan_result = None
        else:
            with st.expander("⚠️ Message Flagged", expanded=True):
                st.warning(f"**Violation Detected**: {result['violation_type']}")
                st.write(f"_{result['violation_details']}_")
                
                st.markdown("### 🤖 AI Suggestion")
                st.info(result['nudge_message'])
                
                if result.get('suggested_rewrite'):
                    st.code(result['suggested_rewrite'], language="text")
                    
                    if st.button("Apply Rewrite"):
                         # This is tricky in Streamlit without rerunning, 
                         # usually requires a callback or session state update to the text area key
                         st.info("Please copy the rewrite above and paste it into the draft area.")
                
                st.divider()
                
                if st.button("🔴 Override & Send Anyway"):
                     try:
                        resp = requests.post(f"{api_url}/workflow/submit", json={
                            "text": draft,
                            "action": "Override",
                            "sender": st.session_state.user,
                            "recipient": recipient,
                            "previous_violation_type": result['violation_type'],
                            "previous_violation_details": result['violation_details']
                        })
                        st.error("Message sent (and flagged for review).")
                        st.session_state.scan_result = None
                     except Exception as e:
                        st.error(f"Error: {e}")

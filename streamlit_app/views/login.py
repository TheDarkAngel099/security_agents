import streamlit as st
import requests

def show(api_url):
    st.markdown("## 🛡️ Security Agent Portal")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("Please sign in to access your dashboard.")
        
        username = st.text_input("Username")
        role_options = {
            "Employee": "employee", 
            "HR Admin": "hr", 
            "Security Lead": "security", 
            "Global Admin": "admin"
        }
        selected_role_label = st.selectbox("Select Role", list(role_options.keys()))
        
        if st.button("Sign In", type="primary", use_container_width=True):
            if username:
                try:
                    role_key = role_options[selected_role_label]
                    response = requests.post(
                        f"{api_url}/auth/login", 
                        json={"username": username, "role": role_key}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.user = data["username"]
                        st.session_state.role = data["role"]
                        st.session_state.token = "dummy_token" # In real app, this would be JWT
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(f"Login failed: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
            else:
                st.warning("Please enter a username.")

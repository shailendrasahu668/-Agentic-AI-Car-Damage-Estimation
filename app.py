# app.py
import streamlit as st
import requests
import warnings

warnings.filterwarnings("ignore")

st.title("🚗 Car Damage Estimator (Multi-Image)")

# Allow multiple file uploads
uploaded_files = st.file_uploader(
    "Upload multiple images of the same car", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.subheader("Uploaded Images")
    cols = st.columns(min(3, len(uploaded_files)))  
    for i, uploaded_file in enumerate(uploaded_files):
        with cols[i % 3]:
            st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)

    if st.button("Estimate Repair"):
        files = []
        for file in uploaded_files:
            files.append(("files", (file.name, file.getvalue(), file.type)))

        try:
            response = requests.post("http://127.0.0.1:8000/predict/", files=files)
            if response.ok:
                result = response.json()
                st.success("✅ Unique Damaged Parts Identified:")
                st.write(result.get("unique_damaged_parts", []))
            else:
                st.error(f"❌ Failed to get estimate: {response.status_code}")
        except Exception as e:
            st.error(f"⚠️ Error connecting to backend: {e}")

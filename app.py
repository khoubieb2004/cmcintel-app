import streamlit as st
import pandas as pd
import requests
from xml.etree import ElementTree
from google.oauth2 import service_account
from gsheetsdb import connect

st.set_page_config(page_title="CMCIntel - AI Excipient Justification", layout="wide")

st.markdown("""
    <style>
        .main {background-color: #f7f9fb;}
        h1, h2, h3 {color: #2c3e50;}
        .stButton>button {
            background-color: #4CAF50; 
            color: white; 
            border: none;
            padding: 0.5em 1em;
            border-radius: 5px;
        }
        .stTextInput>div>div>input {
            border: 1px solid #ccc;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🧪 CMCIntel - AI Excipient Justification")
st.markdown("Justification Generator for **Oral Dosage Forms**")

# Input Section
with st.sidebar:
    st.header("Excipient Entry")
    dosage_form = st.text_input("Oral Dosage Form (e.g. Tablet, Capsule)", "Tablet")
    excipient = st.text_input("Excipient", "Microcrystalline Cellulose")
    formulation_type = st.text_input("Formulation Type", "Immediate-release tablet")
    justification_focus = st.text_area("Excipient Role / Justification Focus", "Binder and filler, improves tablet strength")

    st.markdown("---")
    st.markdown("📤 **Batch Upload**")
    batch_file = st.file_uploader("Upload a CSV file", type=["csv"])
    st.download_button("📥 Download Sample CSV", data=open("CMCIntel_Batch_Template.csv", "rb"), file_name="CMCIntel_Batch_Template.csv")

# Main Form - Justification Display
def generate_justification(excipient, formulation, role):
    summary = f"""
### 🧬 Justification or Scientific Rationale:

The excipient **{excipient}** is included in the {formulation} to serve as a {role.lower()}.

This function supports appropriate product performance, manufacturability, and stability. The inclusion of this excipient aligns with regulatory guidance and QbD principles. Literature supports its safety, compatibility, and effectiveness.

The justification assumes appropriate characterization, pre-formulation, and in-process control have been conducted.
"""
    return summary

if st.button("✅ Generate Justification"):
    st.markdown(generate_justification(excipient, formulation_type, justification_focus))

# Batch mode
if batch_file:
    try:
        df = pd.read_csv(batch_file)
        st.dataframe(df)
        st.markdown("### 📄 Batch Justifications:")
        for index, row in df.iterrows():
            st.markdown(f"#### 🔹 {row['Excipient']} in {row['Formulation Type']}")
            st.markdown(generate_justification(row['Excipient'], row['Formulation Type'], row['Justification Focus']))
    except Exception as e:
        st.error(f"Failed to process the uploaded file: {e}")

# Feedback Section
st.markdown("## 📬 Feedback & Suggestions")
st.write("We would love your feedback to help improve this app!")

st.markdown("📎 **Submit your suggestions using this Google Form:**")
st.markdown("👉 [Open Feedback Form](https://docs.google.com/forms/d/e/1FAIpQLSca_xkR3UAPVOZKUwKa1X9MH_4lEftPgRh61UZt5M8J9izGKA/viewform)")

st.markdown("📋 Or copy the link below to share or paste manually:")
st.code("https://docs.google.com/forms/d/e/1FAIpQLSca_xkR3UAPVOZKUwKa1X9MH_4lEftPgRh61UZt5M8J9izGKA/viewform", language="text")

st.info("Feedback summary not available. Please check Google Sheet connection.")


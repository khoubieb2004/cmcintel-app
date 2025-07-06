import streamlit as st
import pandas as pd
import requests
from xml.etree import ElementTree
import base64

# Patch for Iterable import in gsheetsdb
try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable

from gsheetsdb import connect

# Google Sheet feedback config
conn = connect()

# App title and branding
st.markdown("<h1 style='text-align: center;'>🧪 CMCIntel - AI Excipient Justification</h1>", unsafe_allow_html=True)
st.markdown("---")

# Sidebar input for Single Justification
st.sidebar.header("🧾 Excipient Entry (Oral Dosage Form Only)")
with st.sidebar.form(key="excipient_form"):
    drug = st.text_input("Drug (e.g., Metformin)")
    excipient = st.text_input("Excipient (e.g., MCC)")
    formulation_type = st.text_input("Formulation Type (e.g., Immediate-release tablet)")
    role = st.text_input("Excipient Role (e.g., Disintegrant)")
    example = st.text_area("Example Justification or Concern")
    submit_button = st.form_submit_button(label="Generate Justification")

# Batch Upload
st.markdown("### 📦 Batch Upload")
uploaded_file = st.file_uploader("Upload a CSV file with columns: Drug, Excipient, FormulationType, Role, Example", type="csv")

# PubMed Citation Generator
def get_pubmed_citations(query, count=10):
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": "pubmed",
        "retmode": "json",
        "retmax": count,
        "term": query
    }
    search = requests.get(search_url, params=params).json()
    ids = search.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    summaries = []
    summary_resp = requests.get(fetch_url, params={"db": "pubmed", "retmode": "json", "id": ",".join(ids)}).json()
    for uid in ids:
        info = summary_resp.get("result", {}).get(uid, {})
        title = info.get("title", "No title")
        url = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
        summaries.append(f"- [{title}]({url})")
    return summaries

# Justification Generator
def generate_justification(drug, excipient, formulation_type, role, example):
    header = f"### 📘 Justification or Scientific Rejection:\n"
    core = f"This justification considers the use of **{excipient}** as a **{role}** in **{formulation_type}** formulation of **{drug}**.\n\n"
    if not all([drug, excipient, formulation_type, role]):
        return "❌ Missing input fields. Please complete all sections."

    citations = get_pubmed_citations(f"{excipient} {formulation_type} {role}")
    if citations:
        ref_section = "### 🔍 PubMed References:\n" + "\n".join(citations)
    else:
        ref_section = "⚠️ No PubMed citations found. Please check your query for accuracy."

    return header + core + ref_section

# Single Justification Output
if submit_button and all([drug, excipient, formulation_type, role]):
    output = generate_justification(drug, excipient, formulation_type, role, example)
    st.markdown(output, unsafe_allow_html=True)

# Batch Upload Output
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        for index, row in df.iterrows():
            st.markdown("----")
            st.markdown(f"### Justification {index+1}")
            output = generate_justification(row['Drug'], row['Excipient'], row['FormulationType'], row['Role'], row['Example'])
            st.markdown(output, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Error reading CSV: {e}")

# Feedback section
st.markdown("---")
st.markdown("### 📬 Feedback & Suggestions")
st.markdown("We would love your feedback to help improve this app!")
st.markdown("**🖇️ Submit your suggestions using this Google Form:**\n👉 [Open Feedback Form](https://docs.google.com/forms/d/e/1FAIpQLSca_xkR3UAPVOZKUwKa1X9MH_4lEftPgRh61UZt5M8J9izGKA/viewform?usp=sf_link)")

st.markdown("**📋 Or copy the link below to share or paste manually:**")
st.code("https://docs.google.com/forms/d/e/1FAIpQLSca_xkR3UAPVOZKUwKa1X9MH_4lEftPgRh61UZt5M8J9izGKA/viewform?usp=sf_link")

# Sheet-based feedback summary (coming soon)
st.warning("Feedback summary not available. Please check Google Sheet connection.")

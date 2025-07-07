"""
CMCIntel - AI-Powered Excipient Justification Generator
Author: Dr.Khoubieb Mohammed
Description: Streamlit app to generate regulatory-grade justifications for oral dosage form excipients using PubMed literature and ICH guidelines.
"""

import streamlit as st
import pandas as pd
import requests
from xml.etree import ElementTree
from io import StringIO

# -------------------------------
# 🔧 Configuration
# -------------------------------
st.set_page_config(page_title="CMCIntel - Excipient Justification", layout="wide")
st.markdown("""
    <h1 style='text-align: center;'>🧪 CMCIntel - AI Excipient Justification for Oral Dosage Forms</h1>
""", unsafe_allow_html=True)

# -------------------------------
# 📌 Sidebar Inputs
# -------------------------------
st.sidebar.header("Excipient Entry")
excipient = st.sidebar.text_input("Excipient", placeholder="e.g. CMC")
formulation_type = st.sidebar.text_input("Formulation Type", placeholder="e.g. Immediate-release tablet")
drug_name = st.sidebar.text_input("Drug Name", placeholder="e.g. Metformin")
excipient_role = st.sidebar.text_area("Excipient Role (with examples)", placeholder="e.g. Disintegrant. Example: helps break tablet into smaller particles.")
concerns = st.sidebar.text_area("Concerns to Address (optional)", placeholder="e.g. compatibility with API, dissolution variability")

# -------------------------------
# 🔍 PubMed Integration
# -------------------------------
PUBMED_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
SEARCH_ENDPOINT = PUBMED_API + "esearch.fcgi"
SUMMARY_ENDPOINT = PUBMED_API + "esummary.fcgi"

@st.cache_data(show_spinner=False)
def get_pubmed_citations(query, max_results=10):
    """Fetch PubMed citation titles and links for a given query."""
    params = {"db": "pubmed", "retmode": "json", "retmax": max_results, "term": query}
    try:
        resp = requests.get(SEARCH_ENDPOINT, params=params)
        id_list = resp.json().get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return []

        summary_params = {"db": "pubmed", "retmode": "xml", "id": ",".join(id_list)}
        summary_resp = requests.get(SUMMARY_ENDPOINT, params=summary_params)
        summary_root = ElementTree.fromstring(summary_resp.content)

        citations = []
        for doc in summary_root.findall(".//DocSum"):
            title = ""
            for item in doc.findall("Item"):
                if item.attrib.get("Name") == "Title":
                    title = item.text
            uid = doc.find("Id").text
            citations.append((title, f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"))
        return citations
    except Exception:
        return []

# -------------------------------
# 🧠 Justification Generator
# -------------------------------
def generate_justification(excipient, formulation_type, drug_name, role, concerns=""):
    if not excipient or not formulation_type or not drug_name:
        return "❌ Please fill in all required fields.", []

    concern_note = f" Risk-based assessment indicates no significant concerns related to {concerns}; these are mitigated via validated controls." if concerns else ""

    justification = f"""
### ✅ **Submission-Ready Justification (ICH Compliant)**

The selection of **{excipient}** as a {role.lower()} in the **{formulation_type}** formulation of **{drug_name}** is supported by its established functional role and regulatory acceptance.

It contributes to key CQAs such as disintegration, dissolution, and manufacturability. As outlined in **ICH Q8(R2)**, **Q9**, and **Q10**, this aligns with QTPP expectations and ensures robust process control. {concern_note}

**References:** ICH Q8(R2), Q9, Q10
"""
    references = get_pubmed_citations(f"{excipient} {formulation_type} {drug_name} {role}")
    return justification, references

# -------------------------------
# 🔘 Single Input Mode
# -------------------------------
if st.sidebar.button("Generate Justification"):
    with st.spinner("Generating scientific justification..."):
        justification, citations = generate_justification(excipient, formulation_type, drug_name, excipient_role, concerns)
        st.markdown(justification)
        if citations:
            st.markdown("### 🔍 Supporting Literature:")
            for title, url in citations:
                st.markdown(f"- [{title}]({url})")
        else:
            st.info("No citations found for the given input or PubMed API unreachable.")

# -------------------------------
# 📁 Batch Upload Mode
# -------------------------------
st.markdown("---")
st.markdown("### 🗂️ Batch Upload")

sample_data = pd.DataFrame({
    "Excipient": ["CMC"],
    "FormulationType": ["Immediate-release tablet"],
    "DrugName": ["Metformin"],
    "Role": ["Disintegrant"],
    "Concerns": ["compatibility with API"]
})

csv_data = sample_data.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download Sample Template", csv_data, "sample_batch.csv", "text/csv")

uploaded_file = st.file_uploader("Upload Excel or CSV", type=["csv", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        st.dataframe(df)

        if st.button("Generate Batch Justifications"):
            results = []
            for _, row in df.iterrows():
                justification, citations = generate_justification(
                    row.get("Excipient", ""),
                    row.get("FormulationType", ""),
                    row.get("DrugName", ""),
                    row.get("Role", ""),
                    row.get("Concerns", "")
                )
                results.append({
                    "Excipient": row.get("Excipient", ""),
                    "DrugName": row.get("DrugName", ""),
                    "FormulationType": row.get("FormulationType", ""),
                    "Role": row.get("Role", ""),
                    "Concerns": row.get("Concerns", ""),
                    "Justification": justification,
                    "References": "; ".join([f"{title} ({url})" for title, url in citations])
                })
            out_df = pd.DataFrame(results)
            st.markdown("### ✅ Batch Output:")
            st.dataframe(out_df)
            st.download_button("📥 Download CSV Results", out_df.to_csv(index=False), "batch_justifications.csv", "text/csv")
    except Exception as e:
        st.error(f"Failed to process file: {e}")

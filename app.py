import streamlit as st
import pandas as pd
import requests
from xml.etree import ElementTree

st.set_page_config(page_title="CMCIntel - Excipient Justification", layout="wide")

st.markdown("<h1 style='text-align: center;'>🧪 CMCIntel - AI Excipient Justification for Oral Dosage Forms</h1>", unsafe_allow_html=True)

st.sidebar.header("Excipient Entry")
excipient = st.sidebar.text_input("Excipient", placeholder="e.g. CMC")
formulation_type = st.sidebar.text_input("Formulation Type", placeholder="e.g. Immediate-release tablet")
drug_name = st.sidebar.text_input("Drug Name", placeholder="e.g. Metformin")
excipient_role = st.sidebar.text_area("Excipient Role (with examples)", placeholder="e.g. Disintegrant. Example: helps break tablet into smaller particles.")

pubmed_api = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
summary_endpoint = pubmed_api + "esummary.fcgi"
search_endpoint = pubmed_api + "esearch.fcgi"

def get_pubmed_citations(query):
    params = {
        "db": "pubmed",
        "retmode": "json",
        "retmax": 5,
        "term": query
    }
    search_resp = requests.get(search_endpoint, params=params)
    id_list = search_resp.json().get("esearchresult", {}).get("idlist", [])

    if not id_list:
        return []

    id_str = ",".join(id_list)
    summary_params = {
        "db": "pubmed",
        "retmode": "xml",
        "id": id_str
    }
    summary_resp = requests.get(summary_endpoint, params=summary_params)
    try:
        summary_root = ElementTree.fromstring(summary_resp.content)
        summaries = []
        for docsum in summary_root.findall(".//DocSum"):
            title = ""
            link = ""
            for item in docsum.findall("Item"):
                if item.attrib.get("Name") == "Title":
                    title = item.text
            uid = docsum.find("Id").text
            link = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
            summaries.append((title, link))
        return summaries
    except Exception:
        return []

def generate_justification(excipient, formulation_type, drug_name, excipient_role):
    if not excipient or not formulation_type or not drug_name:
        return "❌ Please fill in all required fields.", []

    justification = f"""
The justification for the use of **{excipient}** in a {formulation_type} formulation of **{drug_name}** involves its established functional role in oral solid dosage forms.

**Excipient Role:** {excipient_role}

**Rationale:**
1. {excipient} is commonly used as a {excipient_role.lower()} in oral formulations.
2. It has demonstrated effectiveness in improving performance parameters (e.g., disintegration, dissolution).
3. Its compatibility with APIs like {drug_name} has been supported in scientific literature.
4. Regulatory guidance recognizes its use in similar formulations.
5. It contributes to patient acceptability, safety, and manufacturability.
6. Risk-benefit analysis supports its inclusion when considering quality and efficacy.

Supporting data from formulation trials, ICH guidelines, and peer-reviewed publications strengthen this justification.

📚 *References shown below may include relevant literature on the excipient role, function, and safety in oral dosage forms.*
"""
    citations = get_pubmed_citations(f"{excipient} {formulation_type} {drug_name} {excipient_role}")
    return justification, citations

if st.sidebar.button("Generate Justification"):
    with st.spinner("Generating..."):
        result, references = generate_justification(excipient, formulation_type, drug_name, excipient_role)
        st.markdown("### 📄 Justification or Scientific Rationale:")
        st.markdown(result)
        if references:
            st.markdown("### 🔍 PubMed References:")
            for title, url in references:
                st.markdown(f"- [{title}]({url})")
        else:
            st.warning("No references found or PubMed API unreachable.")

# 🗂️ Batch Upload Section
st.markdown("---")
st.markdown("### 🗂️ Batch Upload")

# Sample file download link
sample_data = pd.DataFrame({
    "Excipient": ["CMC"],
    "FormulationType": ["Immediate-release tablet"],
    "DrugName": ["Metformin"],
    "Role": ["Disintegrant"]
})
sample_csv = sample_data.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📄 Download Sample CSV Template",
    data=sample_csv,
    file_name="sample_excipient_input.csv",
    mime="text/csv"
)

uploaded_file = st.file_uploader("Upload Excel/CSV file", type=["csv", "xlsx"])
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.dataframe(df)

        if st.button("Generate Batch Justifications"):
            results = []
            for index, row in df.iterrows():
                try:
                    justification, citations = generate_justification(
                        row.get("Excipient", ""),
                        row.get("FormulationType", ""),
                        row.get("DrugName", ""),
                        row.get("Role", "")
                    )
                    results.append({
                        "Excipient": row.get("Excipient", ""),
                        "DrugName": row.get("DrugName", ""),
                        "FormulationType": row.get("FormulationType", ""),
                        "Role": row.get("Role", ""),
                        "Justification": justification,
                        "References": "; ".join([f"{title} ({url})" for title, url in citations])
                    })
                except Exception as e:
                    results.append({
                        "Excipient": row.get("Excipient", ""),
                        "DrugName": row.get("DrugName", ""),
                        "FormulationType": row.get("FormulationType", ""),
                        "Role": row.get("Role", ""),
                        "Justification": f"Error: {str(e)}",
                        "References": ""
                    })
            result_df = pd.DataFrame(results)
            st.markdown("### ✅ Batch Output:")
            st.dataframe(result_df)
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Justifications CSV", csv, "batch_justifications.csv", "text/csv")

    except Exception as e:
        st.error(f"Error processing file: {e}")

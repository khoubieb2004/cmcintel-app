import streamlit as st
import pandas as pd
import requests
from xml.etree import ElementTree
import google.generativeai as genai
from functools import lru_cache

# --- CONFIG ---
st.set_page_config(page_title="CMCIntel Justifier", layout="wide")
st.title("🧪 CMCIntel – AI Excipient Justification for Oral Dosage Forms")

# --- SETUP ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash-latest")

# --- PROMPT TEMPLATE ---
prompt_template = """
You are a senior CMC regulatory writer with expertise in ICH, FDA, and EMA guidelines.
Your task is to generate a high-quality, regulatory-compliant justification for the use of this excipient in an oral drug product formulation.
Input:
- Drug name: {drug_name}
- Excipient: {excipient}
- Formulation type: {formulation_type}
- Role of excipient: {excipient_role}
- Concerns or questions to address: {concerns}
Output:
1. A scientifically sound justification (100–150 words)
2. Include references to ICH Q8/Q9/Q10 where appropriate
3. Add at least 10 PubMed citations with summary bullet points
4. If justification cannot be made, explain clearly with scientific reasoning
5. Tone: formal, precise, submission-ready
"""

# --- PubMed Citation Retrieval ---
@lru_cache(maxsize=128)
def get_pubmed_citations(query, max_results=10):
    try:
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmode": "xml",
            "retmax": max_results,
            "sort": "relevance"
        }
        search_resp = requests.get(base_url, params=search_params)
        xml_root = ElementTree.fromstring(search_resp.content)
        ids = [id_elem.text for id_elem in xml_root.findall(".//Id")]

        citations = []
        for pmid in ids:
            summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            summary_params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
            summary_resp = requests.get(summary_url, params=summary_params)
            try:
                summary_root = ElementTree.fromstring(summary_resp.content)
                title_elem = summary_root.find(".//Item[@Name='Title']")
                if title_elem is not None:
                    citations.append((title_elem.text, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"))
            except Exception:
                continue
        return citations
    except Exception:
        return []

# --- SIDEBAR FORM ---
st.sidebar.header("Excipient Justification Input")
drug_name = st.sidebar.text_input("Drug Name", placeholder="e.g., Metformin")
excipient = st.sidebar.text_input("Excipient", placeholder="e.g., Croscarmellose Sodium")
formulation_type = st.sidebar.text_input("Formulation Type (oral only)", placeholder="e.g., IR tablet")
excipient_role = st.sidebar.text_input("Role of Excipient", placeholder="e.g., Superdisintegrant for rapid breakdown")
concerns = st.sidebar.text_area("Concerns or Questions (optional)", placeholder="e.g., Risk of reduced flowability or chemical instability")

if st.sidebar.button("Generate Justification"):
    if not all([drug_name, excipient, formulation_type, excipient_role]):
        st.error("Please fill in all required fields.")
    else:
        with st.spinner("Generating scientific justification..."):
            prompt = prompt_template.format(
                drug_name=drug_name,
                excipient=excipient,
                formulation_type=formulation_type,
                excipient_role=excipient_role,
                concerns=concerns
            )
            output = gemini.generate_content(prompt)
            st.success("✅ Justification Generated!")
            st.subheader("📄 Scientific Justification:")
            st.write(output.text)
            st.subheader("🔗 Supporting PubMed References:")
            citations = get_pubmed_citations(f"{excipient} oral formulation")
            if citations:
                for i, (title, link) in enumerate(citations, 1):
                    st.markdown(f"**{i}.** [{title}]({link})")
            else:
                st.info("No PubMed citations could be retrieved. Please verify the excipient name or try again later.")

# --- BATCH MODE ---
st.markdown("---")
st.header("📂 Batch Upload for Multiple Justifications")
batch_file = st.file_uploader("Upload CSV", type=["csv"])
st.markdown("[📥 Download Sample Template](https://cmcintel.streamlit.app/sample/CMCIntel_Batch_Template.csv)")

if batch_file:
    df = pd.read_csv(batch_file)
    st.success(f"Uploaded {len(df)} entries. Generating justifications...")
    for _, row in df.iterrows():
        with st.expander(f"{row['Drug Name']} - {row['Excipient']}"):
            prompt = prompt_template.format(
                drug_name=row["Drug Name"],
                excipient=row["Excipient"],
                formulation_type=row["Formulation Type"],
                excipient_role=row["Excipient Role"],
                concerns=row["Concerns"]
            )
            out = gemini.generate_content(prompt)
            st.write(out.text)
            refs = get_pubmed_citations(f"{row['Excipient']} oral formulation")
            for i, (title, link) in enumerate(refs, 1):
                st.markdown(f"{i}. [{title}]({link})")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .reportview-container .main .block-container{ padding-top: 2rem; padding-bottom: 2rem; }
    .sidebar .sidebar-content { background-color: #f5f5f5; }
    h1, h2, h3, h4 { color: #003262; }
    .stButton > button { background-color: #004080; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

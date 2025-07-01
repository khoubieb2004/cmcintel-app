import streamlit as st
import pandas as pd
import requests
from xml.etree import ElementTree
import google.generativeai as genai
from streamlit_extras.stylable_container import stylable_container

# --- CONFIG ---
st.set_page_config(page_title="CMCIntel Justifier", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Segoe UI', sans-serif;
    }
    .block-container {
        padding: 2rem;
    }
    .css-1v0mbdj {  /* stTextInput */
        border: 1px solid #ccc;
        border-radius: 8px;
    }
    .stButton button {
        background-color: #2c6e49;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        padding: 0.5em 1.5em;
    }
    .stButton button:hover {
        background-color: #228b22;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🧪 CMCIntel - AI Excipient Justifier for Oral Formulations")
st.write("""
This tool generates regulatory-compliant justifications for excipients in oral drug formulations, supported by live PubMed references.
""")

# --- SETUP ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash-latest")

# --- PROMPT TEMPLATE ---
prompt_template = """
You are a senior CMC regulatory writer with expertise in ICH, FDA, and EMA guidelines.
Your task is to generate a high-quality, regulatory-compliant justification for the use of this excipient in a drug product formulation.
Input:
- Drug name: {drug_name}
- Excipient: {excipient}
- Formulation type: {formulation_type}
- Role of excipient: {excipient_role}
- Concerns or questions to address: {concerns}
Output:
1. A scientifically sound justification (100-150 words)
2. Include references to ICH Q8/Q9/Q10 where appropriate
3. Add 10 PubMed citations with summary bullet points if available
4. Tone: formal, precise, submission-ready
"""

# --- PUBMED FUNCTION ---
@st.cache_data(show_spinner=False)
def get_pubmed_citations(query, max_results=10):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmode": "xml",
        "retmax": max_results,
        "sort": "relevance"
    }
    try:
        search_resp = requests.get(base_url, params=search_params)
        xml_root = ElementTree.fromstring(search_resp.content)
        ids = [id_elem.text for id_elem in xml_root.findall(".//Id")]
    except Exception:
        return []

    citations = []
    for pmid in ids:
        try:
            summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            summary_params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
            summary_resp = requests.get(summary_url, params=summary_params)
            summary_root = ElementTree.fromstring(summary_resp.content)
            title_elem = summary_root.find(".//Item[@Name='Title']")
            if title_elem is not None:
                citations.append((title_elem.text, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"))
        except Exception:
            continue
    return citations

# --- SINGLE ENTRY ---
st.sidebar.header("🧾 Excipient Entry Form")
drug_name = st.sidebar.text_input("Drug Name")
excipient = st.sidebar.text_input("Excipient")
formulation_type = st.sidebar.text_input("Formulation Type (e.g. IR Tablet, SR Capsule)")
excipient_role = st.sidebar.text_area("Excipient Role", placeholder="e.g. Binder to improve tablet cohesion")
concerns = st.sidebar.text_area("Concerns (optional)", placeholder="e.g. Stability under heat, poor compressibility")

if st.sidebar.button("✨ Generate Justification"):
    with st.spinner("Generating regulatory justification and references..."):
        prompt = prompt_template.format(
            drug_name=drug_name,
            excipient=excipient,
            formulation_type=formulation_type,
            excipient_role=excipient_role,
            concerns=concerns
        )
        output = gemini.generate_content(prompt)
        citations = get_pubmed_citations(f"{excipient} oral pharmaceutical formulation")
        st.success("✅ Justification Complete")

        with stylable_container("card1", css_styles="background: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem"):
            st.subheader("📄 Justification")
            st.markdown(output.text)

        with stylable_container("card2", css_styles="background: #f0f4f8; padding: 1rem; border-radius: 10px"):
            st.subheader("🔗 PubMed References")
            for i, (title, link) in enumerate(citations, 1):
                st.markdown(f"**{i}.** [{title}]({link})")

# --- BATCH MODE ---
st.markdown("---")
st.header("📂 Batch Upload Mode")
st.markdown("[📥 Download CSV Template](https://cmcintel.streamlit.app/sample/CMCIntel_Batch_Template.csv)")
batch_file = st.file_uploader("Upload your CSV file", type=["csv"])

if batch_file:
    df = pd.read_csv(batch_file)
    st.success(f"Uploaded {len(df)} entries")
    for _, row in df.iterrows():
        with stylable_container("batch_card", css_styles="background: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem"):
            st.subheader(f"🧾 {row['Drug Name']} – {row['Excipient']}")
            prompt = prompt_template.format(
                drug_name=row["Drug Name"],
                excipient=row["Excipient"],
                formulation_type=row["Formulation Type"],
                excipient_role=row["Excipient Role"],
                concerns=row["Concerns"]
            )
            output = gemini.generate_content(prompt)
            st.markdown(output.text)
            refs = get_pubmed_citations(f"{row['Excipient']} oral pharmaceutical formulation")
            st.subheader("🔗 PubMed References")
            for i, (title, link) in enumerate(refs, 1):
                st.markdown(f"{i}. [{title}]({link})")

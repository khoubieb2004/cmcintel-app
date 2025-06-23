
import streamlit as st
import pandas as pd
import requests
from xml.etree import ElementTree
import google.generativeai as genai

# --- CONFIG ---
st.set_page_config(page_title="CMCIntel Justifier", layout="centered")
st.title("🧪 CMCIntel - AI Excipient Justification")

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
def get_pubmed_citations(query, max_results=10):
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
        summary_root = ElementTree.fromstring(summary_resp.content)
        title_elem = summary_root.find(".//Item[@Name='Title']")
        if title_elem is not None:
            citations.append((title_elem.text, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"))
    return citations

# --- SIDEBAR FORM ---
st.sidebar.header("Excipient Entry")
drug_name = st.sidebar.text_input("Drug Name")
excipient = st.sidebar.text_input("Excipient")
formulation_type = st.sidebar.selectbox("Formulation Type", ["IR tablet", "SR capsule", "Oral solution", "Parenteral injection"])
excipient_role = st.sidebar.selectbox("Excipient Role", ["Diluent", "Binder", "Disintegrant", "Lubricant", "Co-solvent", "Stabilizer"])
concerns = st.sidebar.text_area("Concerns (optional)")

if st.sidebar.button("Generate Justification"):
    with st.spinner("Generating..."):
        prompt = prompt_template.format(
            drug_name=drug_name,
            excipient=excipient,
            formulation_type=formulation_type,
            excipient_role=excipient_role,
            concerns=concerns
        )
        output = gemini.generate_content(prompt)
        citations = get_pubmed_citations(f"{excipient} pharmaceutical formulation")
        st.success("✅ Justification Generated!")
        st.subheader("📄 Justification:")
        st.write(output.text)
        st.subheader("🔗 PubMed References:")
        for i, (title, link) in enumerate(citations, 1):
            st.markdown(f"**{i}.** [{title}]({link})")

# --- BATCH MODE ---
st.markdown("---")
st.header("📂 Batch Upload")
batch_file = st.file_uploader("Upload CSV", type=["csv"])

if batch_file:
    df = pd.read_csv(batch_file)
    st.success(f"Uploaded {len(df)} entries")
    for _, row in df.iterrows():
        st.markdown(f"### {row['Drug Name']} - {row['Excipient']}")
        prompt = prompt_template.format(
            drug_name=row["Drug Name"],
            excipient=row["Excipient"],
            formulation_type=row["Formulation Type"],
            excipient_role=row["Excipient Role"],
            concerns=row["Concerns"]
        )
        out = gemini.generate_content(prompt)
        st.write(out.text)
        refs = get_pubmed_citations(f"{row['Excipient']} pharmaceutical formulation")
        for i, (title, link) in enumerate(refs, 1):
            st.markdown(f"{i}. [{title}]({link})")

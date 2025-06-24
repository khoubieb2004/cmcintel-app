import streamlit as st
import pandas as pd
import requests
from xml.etree import ElementTree
import google.generativeai as genai
import time

# --- CONFIG ---
st.set_page_config(page_title="CMCIntel Justifier", layout="centered")
st.title("🧪 CMCIntel - AI Excipient Justification for Oral Dosage Forms")

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
1. A scientifically sound justification (100-150 words) or a response if no valid justification exists
2. Include references to ICH Q8/Q9/Q10 where appropriate
3. Add 10 PubMed citations with summary bullet points if available
4. If the justification is weak or unsupported by literature, clearly state this and provide reasoning
5. Tone: formal, precise, submission-ready
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
    try:
        search_resp = requests.get(base_url, params=search_params)
        xml_root = ElementTree.fromstring(search_resp.content)
        ids = [id_elem.text for id_elem in xml_root.findall(".//Id")]
    except Exception:
        return [("PubMed search failed or returned invalid XML.", "https://pubmed.ncbi.nlm.nih.gov")]

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
        time.sleep(0.5)
    return citations

# --- SIDEBAR FORM ---
st.sidebar.header("Excipient Entry (Oral Dosage Form Only)")
drug_name = st.sidebar.text_input("Drug Name")
excipient = st.sidebar.text_input("Excipient")
formulation_type = st.sidebar.selectbox("Formulation Type", ["Immediate-release tablet", "Sustained-release capsule", "Oral solution", "Chewable tablet", "Oral suspension"])
excipient_role = st.sidebar.text_area("Role of Excipient (e.g., Binder to improve tablet cohesion, Lubricant to aid in tablet ejection)")
concerns = st.sidebar.text_area("Concerns (e.g., stability under heat, poor compressibility)")

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
        citations = get_pubmed_citations(f"{excipient} {formulation_type} {excipient_role}")
        st.success("✅ Response Generated!")
        st.subheader("📄 Justification or Scientific Rejection:")
        st.write(output.text)
        st.subheader("🔗 PubMed References:")
        for i, (title, link) in enumerate(citations, 1):
            st.markdown(f"**{i}.** [{title}]({link})")

# --- BATCH MODE ---
st.markdown("---")
st.header("📂 Batch Upload")

with open("CMCIntel_Batch_Template.csv", "rb") as file:
    st.download_button(
        label="📄 Download Sample CSV",
        data=file,
        file_name="CMCIntel_Batch_Template.csv",
        mime="text/csv"
    )
st.caption("Ensure your input is limited to oral dosage forms. Suggested fields: 'Binder to improve compaction', 'Lubricant for manufacturing ease', etc.")

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
        refs = get_pubmed_citations(f"{row['Excipient']} {row['Formulation Type']} {row['Excipient Role']}")
        for i, (title, link) in enumerate(refs, 1):
            st.markdown(f"{i}. [{title}]({link})")

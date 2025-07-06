import streamlit as st
import pandas as pd
import requests
from xml.etree import ElementTree
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIG ---
st.set_page_config(page_title="CMCIntel Justifier", layout="centered")
st.title("🧪 CMCIntel - AI Excipient Justification")

# --- SETUP ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash-latest")

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
        try:
            summary_root = ElementTree.fromstring(summary_resp.content)
            title_elem = summary_root.find(".//Item[@Name='Title']")
            if title_elem is not None:
                citations.append((title_elem.text, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"))
        except:
            continue
    return citations

# --- FORM TEMPLATE ---
prompt_template = '''
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
'''

# --- SIDEBAR FORM ---
st.sidebar.header("Excipient Entry")
drug_name = st.sidebar.text_input("Drug Name")
excipient = st.sidebar.text_input("Excipient")
formulation_type = st.sidebar.text_input("Formulation Type (e.g., IR tablet, SR capsule, chewable, buccal, etc.)")
excipient_role = st.sidebar.text_input("Excipient Role (e.g., disintegrant, stabilizer, diluent)")
concerns = st.sidebar.text_area("Concerns or questions (optional)")

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
        citations = get_pubmed_citations(f"{excipient} {formulation_type}")
        st.success("✅ Justification Generated!")
        st.subheader("📄 Justification:")
        st.write(output.text)
        st.subheader("🔗 PubMed References:")
        for i, (title, link) in enumerate(citations, 1):
            st.markdown(f"**{i}.** [{title}]({link})")

# --- BATCH UPLOAD ---
st.markdown("---")
st.subheader("📂 Batch Upload")
st.markdown("Upload a CSV file with columns: `Drug Name`, `Excipient`, `Formulation Type`, `Excipient Role`, `Concerns`")
batch_file = st.file_uploader("Upload CSV", type="csv")
if batch_file is not None:
    df = pd.read_csv(batch_file)
    st.dataframe(df)
    if st.button("Generate Batch Justifications"):
        with st.spinner("Processing batch..."):
            for index, row in df.iterrows():
                st.markdown(f"---\n### Justification for: **{row['Excipient']} in {row['Drug Name']}**")
                prompt = prompt_template.format(
                    drug_name=row['Drug Name'],
                    excipient=row['Excipient'],
                    formulation_type=row['Formulation Type'],
                    excipient_role=row['Excipient Role'],
                    concerns=row.get('Concerns', '')
                )
                result = gemini.generate_content(prompt)
                st.write(result.text)
                citations = get_pubmed_citations(f"{row['Excipient']} {row['Formulation Type']}")
                st.subheader("🔗 PubMed References:")
                for i, (title, link) in enumerate(citations, 1):
                    st.markdown(f"**{i}.** [{title}]({link})")

# --- FEEDBACK SECTION ---
st.markdown("---")
st.markdown("### 📬 Feedback & Suggestions")
st.markdown(
    '''
We would love your feedback to help improve this app!

🔗 **Submit your suggestions using this Google Form:**  
👉 [Open Feedback Form](https://docs.google.com/forms/d/e/1FAIpQLSca_xkR3UAPVOZKUwKa1X9MH_4lEftPgRh61UZt5M8J9izGKA/viewform?usp=dialog)

📋 Or copy the link below to share or paste manually:
'''
)
feedback_link = "https://docs.google.com/forms/d/e/1FAIpQLSca_xkR3UAPVOZKUwKa1X9MH_4lEftPgRh61UZt5M8J9izGKA/viewform"
st.code(feedback_link, language='text')

# --- FEEDBACK DISPLAY FROM GOOGLE SHEET ---
try:
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gc = gspread.authorize(credentials)
    sh = gc.open_by_url(st.secrets["feedback_sheet_url"])
    worksheet = sh.sheet1
    feedback_data = worksheet.get_all_records()
    df_feedback = pd.DataFrame(feedback_data)

    st.success(f"✅ {len(df_feedback)} feedback submissions received.")
    if not df_feedback.empty:
        st.markdown("#### 📝 Anonymous Feedback Overview")
        st.dataframe(df)

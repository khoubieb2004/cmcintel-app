
!pip install -q google-generativeai


import google.generativeai as genai
from google.colab import userdata

# Replace 'YOUR_API_KEY' with your actual Google API key
GOOGLE_API_KEY = 'AIzaSyDBLW5QRqX_dcmukmiBOvgYAdanrEw_jxA'
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')


excipient_prompt_template = """You are a senior CMC regulatory writer with expertise in ICH, FDA, and EMA guidelines.

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
3. Add 2 PubMed citations with summary bullet points if available
4. Tone: formal, precise, submission-ready
"""



import ipywidgets as widgets
from IPython.display import display

# Dropdowns and text widgets
formulation_dropdown = widgets.Dropdown(
    options=["IR tablet", "Oral solution", "Parenteral injection", "SR capsule"],
    description="Formulation:"
)

role_dropdown = widgets.Dropdown(
    options=["Diluent", "Binder", "Disintegrant", "Lubricant", "Co-solvent", "Stabilizer"],
    description="Excipient Role:"
)

drug_input = widgets.Text(description="Drug:")
excipient_input = widgets.Text(description="Excipient:")
concerns_input = widgets.Textarea(description="Concerns:")

display(drug_input, excipient_input, formulation_dropdown, role_dropdown, concerns_input)



prompt = excipient_prompt_template.format(
    drug_name=drug_input.value,
    excipient=excipient_input.value,
    formulation_type=formulation_dropdown.value,
    excipient_role=role_dropdown.value,
    concerns=concerns_input.value
)

response = gemini_model.generate_content(prompt)

print("\n✅ Justification Output:\n")
print(response.text)


import requests
from xml.etree import ElementTree

def get_pubmed_citations(query, max_results=5):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmode": "xml",
        "retmax": max_results,
        "sort": "relevance"
    }
    search_resp = requests.get(base_url, params=search_params)

    # Add error handling for the search response
    if search_resp.status_code != 200:
        print(f"Error in PubMed search API request: Status code {search_resp.status_code}")
        print(f"Response content: {search_resp.content}")
        return []

    try:
        xml_root = ElementTree.fromstring(search_resp.content)
    except ElementTree.ParseError as e:
        print(f"Error parsing XML from search response: {e}")
        print(f"Response content: {search_resp.content}")
        return []


    ids = [id_elem.text for id_elem in xml_root.findall(".//Id")]
    citations = []

    for pmid in ids:
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        summary_params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
        summary_resp = requests.get(summary_url, params=summary_params)

        # Add error handling for the summary response
        if summary_resp.status_code != 200:
            print(f"Error in PubMed summary API request for PMID {pmid}: Status code {summary_resp.status_code}")
            print(f"Response content: {summary_resp.content}")
            continue # Skip to the next PMID

        try:
            summary_root = ElementTree.fromstring(summary_resp.content)
        except ElementTree.ParseError as e:
            print(f"Error parsing XML from summary response for PMID {pmid}: {e}")
            print(f"Response content: {summary_resp.content}")
            continue # Skip to the next PMID


        title_elem = summary_root.find(".//Item[@Name='Title']")
        if title_elem is not None:
            title = title_elem.text
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            citations.append((title, link))

    return citations

citations = get_pubmed_citations(f"{excipient_input.value} pharmaceutical formulation")
print("\n🔗 Top PubMed Citations:")
for i, (title, link) in enumerate(citations, start=1):
    print(f"{i}. {title}\n   {link}")


from google.colab import files
import pandas as pd

uploaded = files.upload()
df = pd.read_csv(next(iter(uploaded)))

for i, row in df.iterrows():
    prompt = excipient_prompt_template.format(
        drug_name=row["Drug Name"],
        excipient=row["Excipient"],
        formulation_type=row["Formulation Type"],
        excipient_role=row["Excipient Role"],
        concerns=row["Concerns"]
    )
    print(f"\n📘 Justification for {row['Excipient']} in {row['Drug Name']}\n")
    response = gemini_model.generate_content(prompt)
    print(response.text)



from google.colab import drive
drive.mount('/content/drive')

save_path = "/content/drive/MyDrive/CMCIntel_Justification.txt"
with open(save_path, "w") as f:
    f.write(response.text)

print(f"✅ Justification saved to {save_path}")

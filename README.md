# 🧪 CMCIntel – AI Excipient Justifier for Oral Dosage Forms

CMCIntel is a lightweight, AI-powered regulatory writing assistant designed to streamline **excipient justification** for oral pharmaceutical formulations. The app uses **Google Gemini** and **PubMed** to generate ICH-compliant, submission-ready justifications—backed by real scientific references.

## 🚀 Features

✅ Generate excipient justifications in <30 seconds  
✅ Focused on **oral dosage forms** (IR/SR tablets, capsules, etc.)  
✅ Auto-citation from **PubMed** (≥10 high-quality studies)  
✅ Batch CSV upload for large formulation projects  
✅ Explanation if justification fails due to regulatory/scientific mismatch  
✅ Styled for professional, intuitive interaction

---

## 🛠 How It Works

1. You enter the:
   - **Drug name** (e.g., Metformin)
   - **Excipient** (e.g., Croscarmellose Sodium)
   - **Formulation type** (free input)
   - **Excipient role** (with example prompt)
   - Optional concerns/questions

2. The app:
   - Sends the prompt to Gemini
   - Fetches real PubMed references
   - Returns a clean, ~150-word justification with linked citations

---

## 📂 Batch Upload Instructions

1. Download the [CSV Template](https://cmcintel.streamlit.app/sample/CMCIntel_Batch_Template.csv)  
2. Fill in one row per drug-excipient combination  
3. Upload via the app’s **Batch Upload** section  
4. Expand results for each row to view outputs and references

---

## ⚙️ Deployment (Local or Cloud)

### 🔹 Requirements

- Python 3.10+
- `streamlit`, `pandas`, `requests`, `google-generativeai`

### 🔹 Quickstart

```bash
git clone https://github.com/yourusername/cmcintel-app.git
cd cmcintel-app
pip install -r requirements.txt
streamlit run app.py

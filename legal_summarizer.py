import os
from langchain_community.document_loaders import PDFPlumberLoader

PDF_FOLDER = "pdfs"


# =========================
# LOAD TEXT
# =========================
def load_text():

    text = ""

    if not os.path.exists(PDF_FOLDER):
        return "No PDF folder found."

    files = os.listdir(PDF_FOLDER)

    if not files:
        return "No PDF uploaded."

    for file in files:
        if file.endswith(".pdf"):
            path = os.path.join(PDF_FOLDER, file)

            loader = PDFPlumberLoader(path)
            docs = loader.load()

            for doc in docs:
                text += doc.page_content + "\n"

    return text


# =========================
# SUMMARIZER
# =========================
def summarize_document():

    text = load_text()

    if len(text) < 50:
        return "Document too small."

    sentences = text.split(".")

    summary = ". ".join(sentences[:5])

    return summary


# =========================
# CLAUSE FINDER
# =========================
def find_clause(clause):

    text = load_text().lower()

    if not clause:
        return "Enter a clause."

    results = []

    sentences = text.split(".")

    for s in sentences:
        if clause.lower() in s:
            results.append(s.strip())

    if not results:
        return "Clause not found."

    return results[:5]


# =========================
# RISK DETECTOR
# =========================
def detect_risks():

    text = load_text().lower()

    risk_words = [
        "penalty",
        "terminate",
        "liable",
        "fine",
        "breach",
        "damages",
        "lawsuit"
    ]

    found = []

    for word in risk_words:
        if word in text:
            found.append(word)

    if not found:
        return "No risks detected."

    return "Risks found: " + ", ".join(found)

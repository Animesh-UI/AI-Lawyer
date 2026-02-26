import streamlit as st
import os
import matplotlib.pyplot as plt
# import pandas as pd

# RAG
from rag_pipeline import stream_answer
from vector_db import get_vector_db, create_vector_db

# Legal features
from legal_summarizer import (
    summarize_document,
    find_clause,
    detect_risks
)


# Tax
from tax_calculator import *

st.set_page_config(
    page_title="AI Lawyer + Tax Assistant",
    layout="wide"
)

PDF_FOLDER = "pdfs"
os.makedirs(PDF_FOLDER, exist_ok=True)

# =========================
# SESSION STATE
# =========================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "db_ready" not in st.session_state:
    st.session_state.db_ready = False

# =========================
# LOAD FAISS ONCE
# =========================
if not st.session_state.db_ready:
    try:
        db = get_vector_db()
        if db:
            st.session_state.db_ready = True
            print("FAISS Loaded Successfully")
    except Exception as e:
        print("FAISS Load Error:", e)

# =========================
# SIDEBAR
# =========================
menu = st.sidebar.selectbox(
    "Select Tool",
    [
        "AI Lawyer",
        "Legal Summarizer",
        "Clause Finder",
        "Risk Detector",
        "Income Tax Calculator",
        "GST Calculator",
        "TDS Calculator",
        "Business Tax Calculator"
    ]
)

# =========================
# PDF UPLOAD
# =========================
st.sidebar.subheader("Upload PDF")

uploaded_file = st.sidebar.file_uploader(
    "Upload Legal PDF",
    type="pdf"
)

if uploaded_file:
    file_path = os.path.join(PDF_FOLDER, uploaded_file.name)

    if not os.path.exists(file_path):

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.sidebar.success("PDF Uploaded")

        # Rebuild FAISS
        with st.sidebar.spinner("Indexing document..."):
            create_vector_db()

        st.session_state.db_ready = True
        st.sidebar.success("AI Ready!")

    else:
        st.sidebar.info("PDF already exists")

# =========================
# AI LAWYER
# =========================
if menu == "AI Lawyer":

    st.title("⚖️ AI Lawyer Assistant")

    # Show Chat History FIRST
    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    question = st.chat_input("Ask a legal question...")

    if question:

        if not st.session_state.db_ready:
            st.error("Upload a PDF first")
            st.stop()

        # Show user message
        st.session_state.chat_history.append(("user", question))

        with st.chat_message("user"):
            st.markdown(question)

        # AI Response
        response_text = ""

        with st.chat_message("assistant"):
            placeholder = st.empty()

            for chunk in stream_answer(question):
                response_text += chunk
                placeholder.markdown(response_text)

        st.session_state.chat_history.append(
            ("assistant", response_text)
        )

# =========================
# SUMMARIZER
# =========================
elif menu == "Legal Summarizer":

    st.title("📄 Document Summarizer")

    if st.button("Summarize Document"):

        if not st.session_state.db_ready:
            st.error("Upload PDF first")
        else:
            with st.spinner("Analyzing..."):
                summary = summarize_document()

            st.success("Summary Ready")
            st.markdown(summary)

# =========================
# CLAUSE FINDER
# =========================
elif menu == "Clause Finder":

    st.title("🔎 Clause Finder")

    clause = st.text_input(
        "Enter clause name",
        placeholder="termination, penalty, rent..."
    )

    if st.button("Find Clause"):

        if not st.session_state.db_ready:
            st.error("Upload PDF first")
        else:
            with st.spinner("Searching..."):
                result = find_clause(clause)

            st.markdown(result)

# =========================
# RISK DETECTOR
# =========================
elif menu == "Risk Detector":

    st.title("⚠️ Risk Detection")

    if st.button("Detect Risks"):

        if not st.session_state.db_ready:
            st.error("Upload PDF first")
        else:
            with st.spinner("Analyzing risks..."):
                risks = detect_risks()

            st.markdown(risks)

# =========================
# INCOME TAX
# =========================
elif menu == "Income Tax Calculator":

    st.title("💰 Income Tax Calculator")

    col1, col2 = st.columns(2)

    with col1:
        income = st.number_input("Annual Income", value=800000)
        basic = st.number_input("Basic Salary", value=300000)
        hra_received = st.number_input("HRA Received", value=100000)
        rent = st.number_input("Rent Paid", value=120000)

    with col2:
        sec80c = st.number_input("80C Deduction", value=50000)
        sec80d = st.number_input("80D Deduction", value=25000)
        metro = st.checkbox("Metro City")

    if st.button("Calculate Tax"):

        hra = hra_deduction(
            basic,
            hra_received,
            rent,
            metro
        )

        old_tax, old_taxable = old_regime_tax(
            income,
            hra,
            sec80c,
            sec80d
        )

        new_tax, new_taxable = new_regime_tax(
            income
        )

        st.subheader("Results")

        st.write("HRA Deduction:", hra)
        st.write("Standard Deduction:", STANDARD_DEDUCTION)
        st.write("Old Tax:", old_tax)
        st.write("New Tax:", new_tax)

        fig, ax = plt.subplots()
        ax.bar(["Old Tax", "New Tax"], [old_tax, new_tax])
        st.pyplot(fig)

        data = {
            "Income": income,
            "HRA": hra,
            "80C": sec80c,
            "80D": sec80d,
            "Old Tax": old_tax,
            "New Tax": new_tax
        }

        file = export_pdf(data)

        with open(file, "rb") as f:
            st.download_button(
                "Download PDF",
                f,
                file_name=file
            )

# =========================
# GST
# =========================
elif menu == "GST Calculator":

    st.title("GST Calculator")

    amount = st.number_input("Amount", value=1000)
    gst_rate = st.number_input("GST %", value=18)

    if st.button("Calculate GST"):

        gst, total = gst_calculator(
            amount,
            gst_rate
        )

        st.write("GST:", gst)
        st.write("Total:", total)

# =========================
# TDS
# =========================
elif menu == "TDS Calculator":

    st.title("TDS Calculator")

    amount = st.number_input("Amount", value=50000)
    rate = st.number_input("TDS %", value=10)

    if st.button("Calculate TDS"):

        tds = tds_calculator(
            amount,
            rate
        )

        st.write("TDS:", tds)

# =========================
# BUSINESS TAX
# =========================
elif menu == "Business Tax Calculator":

    st.title("Business Tax Calculator")

    profit = st.number_input("Profit", value=500000)

    if st.button("Calculate Business Tax"):

        tax = business_tax(profit)

        st.write("Business Tax:", tax)

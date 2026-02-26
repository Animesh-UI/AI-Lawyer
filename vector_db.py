import os
import shutil
import time
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

PDF_FOLDER = "pdfs"
FAISS_PATH = "faiss_index"

os.makedirs(PDF_FOLDER, exist_ok=True)

# Embedding model
embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")

# Cache DB in memory
faiss_db = None


# -------------------------
# Load PDFs
# -------------------------
def load_documents():
    documents = []

    for file in os.listdir(PDF_FOLDER):
        if file.endswith(".pdf"):
            path = os.path.join(PDF_FOLDER, file)
            print("Loading:", file)

            try:
                loader = PDFPlumberLoader(path)
                documents.extend(loader.load())
            except Exception as e:
                print("Error loading", file, ":", e)

    return documents


# -------------------------
# Split Text
# -------------------------
def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    return splitter.split_documents(documents)


# -------------------------
# Delete FAISS safely
# -------------------------
def safe_delete(path):
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            time.sleep(1)
            print("Old FAISS deleted")
        except Exception as e:
            print("FAISS delete error:", e)


# -------------------------
# Create FAISS
# -------------------------
def create_vector_db():
    global faiss_db

    # If already loaded → don't rebuild
    if faiss_db is not None:
        print("FAISS already loaded")
        return faiss_db

    # If exists on disk → load it
    if os.path.exists(FAISS_PATH):
        print("Loading existing FAISS index...")
        return load_vector_db()

    print("Creating FAISS index...")

    docs = load_documents()

    if not docs:
        print("No documents found")
        return None

    chunks = split_documents(docs)

    print("Chunks:", len(chunks))

    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(FAISS_PATH)

    faiss_db = db

    print("FAISS ready")
    return db


# -------------------------
# Load FAISS
# -------------------------
def load_vector_db():
    global faiss_db

    # Use cached DB
    if faiss_db is not None:
        return faiss_db

    index_file = os.path.join(FAISS_PATH, "index.faiss")

    # If index does not exist → create
    if not os.path.exists(index_file):
        print("FAISS index not found. Creating new index...")
        return create_vector_db()

    try:
        print("Loading FAISS...")

        db = FAISS.load_local(
            FAISS_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )

        faiss_db = db
        print("FAISS loaded successfully")

        return db

    except Exception as e:
        print("FAISS load failed:", e)
        print("Rebuilding FAISS...")
        return create_vector_db()


# -------------------------
# Get DB
# -------------------------
def get_vector_db():
    return load_vector_db()

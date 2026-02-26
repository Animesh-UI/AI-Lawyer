from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from vector_db import get_vector_db

# =========================
# BETTER MODEL SETTINGS
# =========================
llm_model = ChatOllama(
    model="tinyllama",
    temperature=0.1,        # More accurate answers
    num_predict=2000,       # Prevents cut answers
    top_k=30,
    top_p=0.95,
    repeat_penalty=1.15,
    streaming=True
)

# =========================
# LAZY LOAD DB
# =========================
_db = None

def get_db():
    global _db
    if _db is None:
        try:
            _db = get_vector_db()
        except Exception as e:
            print("DB Load Error:", e)
            return None
    return _db


# =========================
# RETRIEVE DOCS
# =========================
def retrieve_docs(query):
    db = get_db()

    if db is None:
        return []

    try:
        # More context = better legal answers
        docs = db.similarity_search(query, k=5)
        return docs
    except Exception as e:
        print("Search Error:", e)
        return []


# =========================
# CONTEXT BUILDER
# =========================
def get_context(docs):

    if not docs:
        return ""

    context_parts = []

    for i, doc in enumerate(docs):
        context_parts.append(f"Document {i+1}:\n{doc.page_content}")

    context = "\n\n".join(context_parts)

    # Larger context improves answers
    return context[:4000]


# =========================
# LAWYER PROMPT
# =========================
prompt = ChatPromptTemplate.from_template("""
You are an experienced professional lawyer.

Answer like a real lawyer using clear legal reasoning.

Follow this structure strictly:

1. Legal Issue  
State the legal question.

2. Relevant Law  
Mention applicable laws or principles.

3. Analysis  
Apply the law to the facts.

4. Conclusion  
Give a clear final answer.

Rules:
- Give complete answers
- Do NOT stop mid sentence
- Be professional
- Use only provided context
- If context missing, say clearly

Context:
{context}

Question:
{question}

Legal Answer:
""")

chain = prompt | llm_model


# =========================
# NORMAL ANSWER
# =========================
def answer_query(question):

    if not question.strip():
        return "Enter a question."

    docs = retrieve_docs(question)

    if not docs:
        return "No PDF content found. Upload PDF first."

    context = get_context(docs)

    try:
        response = chain.invoke({
            "context": context,
            "question": question
        })

        if hasattr(response, "content"):
            return response.content

        return str(response)

    except Exception as e:
        return f"Error: {str(e)}"


# =========================
# STREAMING ANSWER
# =========================
def stream_answer(question):

    if not question.strip():
        yield "Enter a question."
        return

    docs = retrieve_docs(question)

    if not docs:
        yield "No PDF content found. Upload PDF first."
        return

    context = get_context(docs)

    try:
        stream = chain.stream({
            "context": context,
            "question": question
        })

        full_response = ""

        for chunk in stream:
            if hasattr(chunk, "content") and chunk.content:
                full_response += chunk.content
                yield chunk.content

        # Retry if answer incomplete
        if len(full_response) < 100:
            retry = chain.invoke({
                "context": context,
                "question": question
            })

            if hasattr(retry, "content"):
                yield retry.content

    except Exception as e:
        yield f"Error: {str(e)}"

import streamlit as st

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from rbac import has_access

st.set_page_config(page_title="Enterprise Intelligence Copilot")

st.title("Enterprise Intelligence Copilot")

role = st.sidebar.selectbox(
    "Select Role",
    [
        "employee",
        "manager",
        "compliance_officer",
        "admin"
    ]
)

query = st.text_input(
    "Ask your enterprise question"
)

if query:

    vectordb = Chroma(
        persist_directory="./chroma_db",
        embedding_function=OpenAIEmbeddings()
    )

    docs = vectordb.similarity_search_with_score(
        query,
        k=5
    )

    authorized_docs = []

    retrieval_trace = []

    for doc, score in docs:

        source = doc.metadata.get(
            "source",
            "unknown"
        )

        if has_access(role, source):

            authorized_docs.append(doc)

            retrieval_trace.append(
                {
                    "source": source,
                    "score": round(score, 3)
                }
            )

    if not authorized_docs:

        st.error(
            "Access denied or no authorized documents found."
        )

        st.stop()

    context = "\n\n".join(
        [d.page_content for d in authorized_docs]
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )

    prompt = f"""
You are an enterprise assistant.

Answer ONLY from provided context.

If answer not found, say:
'Insufficient evidence.'

Context:
{context}

Question:
{query}

Provide:
1. Answer
2. Sources used
3. Confidence estimate
"""

    response = llm.invoke(prompt)

    st.subheader("Answer")

    st.write(response.content)

    st.subheader("Retrieval Trace")

    st.json(retrieval_trace)

    confidence = min(
        95,
        60 + len(authorized_docs) * 5
    )

    st.metric(
        "Confidence",
        f"{confidence}%"
    )
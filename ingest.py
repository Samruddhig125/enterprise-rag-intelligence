from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

import pandas as pd
import json


documents = []

# PDF

pdf_loader = PyPDFLoader("data/compliance.pdf")
documents.extend(pdf_loader.load())

# CSV

employees = pd.read_csv("data/employees.csv")

for _, row in employees.iterrows():
    documents.append(
        {
            "page_content": str(row.to_dict()),
            "metadata": {"source": "employees.csv"}
        }
    )

# INCIDENTS

incidents = pd.read_csv("data/incidents.csv")

for _, row in incidents.iterrows():
    documents.append(
        {
            "page_content": str(row.to_dict()),
            "metadata": {"source": "incidents.csv"}
        }
    )

# JSON

with open("data/audit_logs.json") as f:
    logs = json.load(f)

for log in logs:
    documents.append(
        {
            "page_content": str(log),
            "metadata": {"source": "audit_logs.json"}
        }
    )


splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

chunks = splitter.create_documents(
    [d["page_content"] if isinstance(d, dict) else d.page_content for d in documents]
)

vectordb = Chroma.from_documents(
    chunks,
    OpenAIEmbeddings(),
    persist_directory="./chroma_db"
)

vectordb.persist()

print("Done")
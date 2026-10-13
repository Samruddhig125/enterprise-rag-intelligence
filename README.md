#  Enterprise RAG Intelligence System


---
###Link to the project
 <a href="https://enterprise-rag-intelligence-fymztke7sbehtqjxut7phq.streamlit.app/">Live</a>

##  Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI (app.py)                       |
│   Role Login → Query Input → Response Display → Citations      │
└───────────────────────┬────────────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────────────┐
│               ENTERPRISE PIPELINE (core/pipeline.py)           │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  RBAC Engine │  │ Query Router │  │  Ingestion Engine    │  │
│  │  (rbac.py)   │  │(retrieval.py)│  │  (ingestion.py)      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                     │              │
│         ▼                 ▼                     ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          VECTOR STORE (ChromaDB + MiniLM-L6-v2)          │  │
│  │     Semantic search → RBAC post-filter → Top-K chunks    │  │
│  └──────────────────────────┬───────────────────────────────   │
│                             │                                  │
│                             ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         GENERATION ENGINE                               |   │
│  │   Grounded response + Citations + Confidence scoring    │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

##  Project Structure

```
enterprise_rag/
├── app.py                    # Streamlit application
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── pipeline.py           # Main orchestrator
│   ├── rbac.py               # Role-based access control
│   ├── ingestion.py          # Multi-format data ingestion
│   ├── retrieval.py          # Vector store + query router
│   └── generation.py         
└── data/
    ├── generate_data.py      # Synthetic dataset generator
    ├── rbac_policy.json      # Access control policies
    ├── pdfs/                 # PDF document texts
    │   ├── Q4_Financial_Report_2024.txt
    │   ├── HR_Policy_Handbook_2024.txt
    │   └── IT_Security_Policy_2024.txt
    ├── csv/
    │   ├── employees.csv
    │   ├── vendor_contracts.csv
    │   └── it_assets.csv
    ├── json_logs/
    │   ├── security_audit_logs.json
    │   └── application_logs.json
    └── reports/
        ├── Operations_Summary_Dec2024.txt
        └── Compliance_Audit_2024.txt
```



## 👥 Test Users & Roles

| Username | Role | Access Level |
|----------|------|-------------|
| `sarah.mitchell` | Executive |  All sources |
| `bob.martinez` | Finance |  Financial docs + CSVs |
| `james.okafor` | HR |  HR policy + employee data |
| `dr.priya.nair` | IT Security |  Security logs + IT policy |
| `marcus.chen` | Operations |  Ops reports + app logs |
| `henry.park` | Employee |  HR handbook only |

---

##  RBAC Demo — Try These Queries

### As `henry.park` (Employee) — will be DENIED:
- *"What was our Q4 revenue?"* →  Access Denied
- *"Show me security audit logs"* →  Access Denied

### As `bob.martinez` (Finance) — will SUCCEED:
- *"What is our Q4 2024 EBITDA?"* →  Grounded answer from financial report
- *"Which vendor contracts are expiring?"* →  Answer from CSV data

### As `dr.priya.nair` (IT Security) — will SUCCEED:
- *"How many unauthorized access attempts were logged?"* → Answer from security logs
- *"What are our CVE patching SLAs?"* →  Answer from IT policy doc

### As `sarah.mitchell` (Executive) — full access:
- *"Summarize our compliance posture and any GDPR findings"* →  Multi-source answer

---

##  Core Technical Features

### 1. Intelligent Retrieval
- **Semantic Search**: `all-MiniLM-L6-v2` embeddings via ChromaDB
- **Query Routing**: Keyword-based intent classification routes queries to relevant source types before vector search
- **Fallback search**: If routed search returns <2 results, automatically falls back to full corpus search
- **Cross-source synthesis**: Top-K chunks from multiple source types are combined into a single context window

### 2. Strict RBAC
- **Pre-query check**: Query intent analyzed for sensitive keywords before retrieval
- **Post-retrieval filter**: Every retrieved chunk checked against user's role permissions
- **No leakage**: Unauthorized documents never enter the LLM context
- **Granular policies**: Per-role allowed/denied source lists + field-level redaction

### 3. Grounded Generation
- **System prompt engineering**: Claude instructed to ONLY use provided context, cite sources
- **Citation injection**: Context sections tagged [1]–[6] for citation in response
- **Hallucination minimization**: Explicit system prompt rule — acknowledge gaps, never guess

### 4. Explainability
- **Confidence score**: Heuristic based on retrieval similarity + source diversity + hedging detection
- **Retrieval trace**: Full trace of which chunks were used, their scores, and source metadata
- **Query routing disclosure**: Shows which data domain the query was routed to
- **Citation pills**: Each source shown with relevance score, classification level, and section

---

##  Data Sources Covered

| Type | Files | Classification |
|------|-------|---------------|
| PDF/Document | Q4 Financial Report, HR Policy, IT Security Policy, Compliance Audit, Ops Summary | CONFIDENTIAL / INTERNAL |
| CSV | Employee Directory (15 records), Vendor Contracts (6), IT Assets (8) | CONFIDENTIAL / INTERNAL |
| JSON Logs | Security Audit Logs (50 events), Application Logs (40 entries) | CONFIDENTIAL / INTERNAL |

---

##  Tech Stack

| Component | Technology | Why |
|-----------|------------|-----|
| UI | Streamlit | Zero-setup, rapid deployment |
| Embeddings | `all-MiniLM-L6-v2` | Fast, high-quality, local |
| Vector DB | ChromaDB | Persistent, no server needed |
| RBAC | Custom Python | No infra dependency, fully auditable |
| Data | Pure Python (CSV, JSON, text) | No DB server required |

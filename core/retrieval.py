"""
Vector Store & Retrieval Engine
Uses ChromaDB for persistent vector storage with sentence-transformer embeddings.
Enforces RBAC during retrieval — no unauthorized chunks ever reach the LLM.
"""

import os
import hashlib
from typing import Optional
import chromadb
from chromadb.utils import embedding_functions
from core.ingestion import DataChunk, DataIngestionEngine
from core.rbac import RBACEngine, User


#  RETRIEVAL RESULT 

class RetrievalResult:
    def __init__(self, chunk: DataChunk, score: float, rank: int):
        self.chunk = chunk
        self.score = score          # cosine similarity (0–1, higher = better)
        self.rank = rank
        self.relevance_label = self._label(score)

    def _label(self, score: float) -> str:
        if score >= 0.75:   return "High"
        if score >= 0.55:   return "Medium"
        return "Low"


#  VECTOR STORE ENGINE 

class VectorStoreEngine:
    COLLECTION_NAME = "enterprise_rag"
    EMBED_MODEL = "all-MiniLM-L6-v2"  # Fast, lightweight, good quality

    def __init__(self, persist_dir: str = ".chromadb"):
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.EMBED_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )
        # We keep a local map of chunk_id → DataChunk for full metadata access
        self._chunk_map: dict[str, DataChunk] = {}

    def is_indexed(self) -> bool:
        return self.collection.count() > 0

    def index_chunks(self, chunks: list[DataChunk], batch_size: int = 64):
        """Upsert all chunks into ChromaDB"""
        print(f"[VectorStore] Indexing {len(chunks)} chunks...")
        ids, docs, metas = [], [], []

        for chunk in chunks:
            safe_id = hashlib.md5(chunk.chunk_id.encode()).hexdigest()
            self._chunk_map[safe_id] = chunk
            ids.append(safe_id)
            docs.append(chunk.content[:2000])  # Chroma has a limit
            metas.append({
                "source_name": chunk.source_name,
                "source_file": chunk.source_file,
                "source_type": chunk.source_type,
                "department": chunk.department,
                "classification": chunk.classification,
                "page_or_row": chunk.page_or_row,
                "chunk_id_orig": chunk.chunk_id,
            })

        # Batch upsert
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i:i + batch_size],
                documents=docs[i:i + batch_size],
                metadatas=metas[i:i + batch_size],
            )
        print(f"[VectorStore] Indexed {len(chunks)} chunks successfully.")

    def rebuild_chunk_map(self, chunks: list[DataChunk]):
        """Restore in-memory chunk map from already-indexed data"""
        for chunk in chunks:
            safe_id = hashlib.md5(chunk.chunk_id.encode()).hexdigest()
            self._chunk_map[safe_id] = chunk

    def retrieve(
        self,
        query: str,
        user: User,
        rbac: RBACEngine,
        top_k: int = 8,
        source_type_filter: Optional[str] = None,
    ) -> list[RetrievalResult]:
        """
        Semantic retrieval with post-retrieval RBAC filtering.
        Retrieves top_k * 3 candidates, then filters to permitted sources.
        """
        candidates_k = min(top_k * 4, self.collection.count())
        if candidates_k == 0:
            return []

        query_kwargs = {"query_texts": [query], "n_results": candidates_k}
        if source_type_filter:
            query_kwargs["where"] = {"source_type": source_type_filter}

        results = self.collection.query(**query_kwargs)

        ids = results["ids"][0]
        distances = results["distances"][0]  # cosine distance (0=identical, 2=opposite)
        metas = results["metadatas"][0]

        permitted = []
        for doc_id, dist, meta in zip(ids, distances, metas):
            source_name = meta.get("source_name", "")
            source_file = meta.get("source_file", "")

            # RBAC check — skip if not permitted
            if not rbac.can_access_chunk(user, source_name, source_file):
                continue

            # Convert cosine distance to similarity score
            similarity = 1.0 - (dist / 2.0)

            chunk = self._chunk_map.get(doc_id)
            if chunk is None:
                # Reconstruct minimal chunk from metadata
                chunk = DataChunk(
                    chunk_id=meta.get("chunk_id_orig", doc_id),
                    content=results["documents"][0][ids.index(doc_id)] if "documents" in results else "",
                    source_name=source_name,
                    source_file=source_file,
                    source_type=meta.get("source_type", "unknown"),
                    department=meta.get("department", ""),
                    classification=meta.get("classification", ""),
                    page_or_row=meta.get("page_or_row", ""),
                )

            permitted.append(RetrievalResult(chunk=chunk, score=similarity, rank=0))

            if len(permitted) >= top_k:
                break

        # Assign ranks
        for i, r in enumerate(permitted):
            r.rank = i + 1

        return permitted

    def get_source_diversity(self, results: list[RetrievalResult]) -> dict:
        """Analyze which sources are represented in results"""
        sources = {}
        for r in results:
            sname = r.chunk.source_name
            if sname not in sources:
                sources[sname] = {"count": 0, "type": r.chunk.source_type, "dept": r.chunk.department}
            sources[sname]["count"] += 1
        return sources

    def total_chunks(self) -> int:
        return self.collection.count()


#  QUERY ROUTER 

class QueryRouter:
    """
    Classifies the user's query to route it to the most relevant source type(s).
    Uses keyword heuristics + fallback to full corpus.
    """

    ROUTE_KEYWORDS = {
        "financial": ["revenue", "profit", "budget", "ebitda", "q4", "q1", "earnings", "cost",
                       "financial", "forecast", "margin", "cash flow", "vendor", "contract"],
        "hr": ["employee", "salary", "leave", "policy", "hire", "onboard", "performance",
               "bonus", "headcount", "remote", "compensation", "hr", "department"],
        "security": ["security", "vulnerability", "incident", "breach", "cve", "mfa",
                     "access log", "audit", "unauthorized", "login", "password", "patch"],
        "operations": ["uptime", "latency", "deployment", "incident", "server", "api",
                       "infrastructure", "capacity", "outage", "monitoring", "logs"],
        "compliance": ["gdpr", "ccpa", "sox", "audit", "compliance", "regulation", "dsar",
                       "data subject", "penalty", "fine", "privacy"],
        "it": ["asset", "laptop", "server", "hardware", "device", "ip address", "network", "vpn"],
    }

    ROUTE_TO_SOURCE_TYPE = {
        "financial": None,   # search all (finance docs + csv)
        "hr": None,
        "security": "json",  # prefer security logs
        "operations": None,
        "compliance": None,
        "it": "csv",
    }

    def classify(self, query: str) -> tuple[str, Optional[str]]:
        """Returns (route_label, optional_source_type_filter)"""
        q = query.lower()
        scores = {}
        for route, keywords in self.ROUTE_KEYWORDS.items():
            scores[route] = sum(1 for kw in keywords if kw in q)

        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return "general", None

        source_type = self.ROUTE_TO_SOURCE_TYPE.get(best)
        return best, source_type

    def explain_routing(self, route: str) -> str:
        explanations = {
            "financial": "📊 Routed to Financial Reports & Vendor Data",
            "hr": "👥 Routed to HR Policies & Employee Records",
            "security": "🔐 Routed to Security Logs & IT Policies",
            "operations": "⚙️ Routed to Operations Reports & App Logs",
            "compliance": "⚖️ Routed to Compliance & Audit Documents",
            "it": "💻 Routed to IT Asset Inventory",
            "general": "🔍 Full corpus search across all sources",
        }
        return explanations.get(route, "🔍 General search")
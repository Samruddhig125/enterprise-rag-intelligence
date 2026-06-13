"""
Enterprise RAG Pipeline — Main Orchestrator
Wires together: Ingestion → Indexing → Routing → Retrieval → RBAC → Generation
"""

import os
import streamlit as st
from core.ingestion import DataIngestionEngine
from core.retrieval import VectorStoreEngine, QueryRouter
from core.generation import GenerationEngine, RAGResponse
from core.rbac import RBACEngine, User


class EnterprisePipeline:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.rbac = RBACEngine(policy_path=os.path.join(data_dir, "rbac_policy.json"))
        self.router = QueryRouter()
        self.ingestion = DataIngestionEngine(data_dir=data_dir)
        self.vector_store = VectorStoreEngine(persist_dir=".chromadb")
        self.generator = GenerationEngine()

    def initialize(self, force_reindex: bool = False):
        """
        One-time setup: ingest all data and build the vector index.
        Subsequent runs use the persisted ChromaDB index.
        """
        if self.vector_store.is_indexed() and not force_reindex:
            # Index already exists — just rebuild the in-memory chunk map
            chunks = self.ingestion.ingest_all()
            self.vector_store.rebuild_chunk_map(chunks)
            return {
                "status": "loaded",
                "chunk_count": self.vector_store.total_chunks(),
                "source_stats": self.ingestion.get_source_stats(),
            }

        # Fresh index
        chunks = self.ingestion.ingest_all()
        self.vector_store.index_chunks(chunks)
        return {
            "status": "indexed",
            "chunk_count": len(chunks),
            "source_stats": self.ingestion.get_source_stats(),
        }

    def query(
        self,
        query_text: str,
        username: str,
        top_k: int = 6,
    ) -> dict:
        """
        Full RAG pipeline:
        1. Authenticate user
        2. RBAC pre-check on query intent
        3. Route query → pick source filter
        4. Semantic retrieval with RBAC post-filter
        5. Generate grounded response
        6. Return structured result
        """

        # 1. User authentication
        user = self.rbac.get_user(username)
        if not user:
            return {"error": f"User '{username}' not found in the system."}

        # 2. RBAC pre-check
        access = self.rbac.check_query_sensitivity(user, query_text)
        if not access.allowed:
            return {
                "error": access.reason,
                "access_denied": True,
                "user": user,
            }

        # 3. Query routing
        route_label, source_type_filter = self.router.classify(query_text)
        route_explanation = self.router.explain_routing(route_label)

        # 4. Retrieve with RBAC
        results = self.vector_store.retrieve(
            query=query_text,
            user=user,
            rbac=self.rbac,
            top_k=top_k,
            source_type_filter=source_type_filter,
        )

        # If filtered results are too few, fall back to full search
        if len(results) < 2 and source_type_filter:
            results = self.vector_store.retrieve(
                query=query_text,
                user=user,
                rbac=self.rbac,
                top_k=top_k,
                source_type_filter=None,
            )

        # 5. Generate response
        rag_response = self.generator.generate(
            query=query_text,
            retrieval_results=results,
            user=user,
            route_label=route_label,
            route_explanation=route_explanation,
            redacted_fields=access.redacted_fields,
        )

        return {"response": rag_response, "user": user, "access": access}

    def get_user_list(self) -> list[dict]:
        return self.rbac.get_all_users()
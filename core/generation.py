"""
RAG Generation Engine
Calls OpenAI API with retrieved context to generate grounded,
cited, hallucination-minimized responses with confidence indicators.
"""

import os
from datetime import datetime
from openai import OpenAI
from core.retrieval import RetrievalResult
from dotenv import load_dotenv
load_dotenv()
from core.rbac import User


#  RESPONSE MODEL 

class RAGResponse:
    def __init__(
        self,
        answer: str,
        citations: list,
        sources_used: list,
        confidence: float,
        confidence_label: str,
        route_label: str,
        route_explanation: str,
        retrieval_results: list,
        query: str,
        user,
        timestamp: str,
        tokens_used: int = 0,
    ):
        self.answer = answer
        self.citations = citations
        self.sources_used = sources_used
        self.confidence = confidence
        self.confidence_label = confidence_label
        self.route_label = route_label
        self.route_explanation = route_explanation
        self.retrieval_results = retrieval_results
        self.query = query
        self.user = user
        self.timestamp = timestamp
        self.tokens_used = tokens_used


#  GENERATION ENGINE 


class GenerationEngine:
    MODEL = "gpt-4o"

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)

    def generate(
        self,
        query: str,
        retrieval_results: list,
        user,
        route_label: str,
        route_explanation: str,
        redacted_fields: list = [],
    ) -> RAGResponse:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not retrieval_results:
            return RAGResponse(
                answer="I couldn't find relevant information for your query in the sources you have access to. This may be because the information is restricted for your role, or doesn't exist in the knowledge base.",
                citations=[],
                sources_used=[],
                confidence=0.0,
                confidence_label="No Data",
                route_label=route_label,
                route_explanation=route_explanation,
                retrieval_results=[],
                query=query,
                user=user,
                timestamp=timestamp,
            )

        # Build context block from retrieved chunks
        context_sections = []
        citations = []
        seen_sources = []

        for i, result in enumerate(retrieval_results[:6]):
            chunk = result.chunk
            cite_id = f"[{i+1}]"
            context_sections.append(
                f"{cite_id} SOURCE: {chunk.source_name}\n"
                f"Type: {chunk.source_type.upper()} | Dept: {chunk.department} | "
                f"Section: {chunk.page_or_row} | Relevance: {result.relevance_label} ({result.score:.2f})\n"
                f"---\n{chunk.content}\n"
            )
            citations.append({
                "id": cite_id,
                "source": chunk.source_name,
                "file": chunk.source_file,
                "type": chunk.source_type,
                "section": chunk.page_or_row,
                "relevance_score": round(result.score, 3),
                "relevance_label": result.relevance_label,
                "classification": chunk.classification,
                "department": chunk.department,
            })
            if chunk.source_name not in seen_sources:
                seen_sources.append(chunk.source_name)

        context_text = "\n\n".join(context_sections)

        redaction_notice = ""
        if redacted_fields:
            redaction_notice = f"\n\nNOTE: The following fields are redacted for this user's role: {', '.join(redacted_fields)}. Do not include specific values for these in your response."

        system_prompt = f"""You are an Enterprise AI Assistant for ACME Corporation — a secure, intelligent RAG system.

Your role is to answer employee questions using ONLY the provided source context. You are grounded, precise, and transparent.

STRICT RULES:
1. ONLY use information from the provided context sections. Never hallucinate or infer beyond the context.
2. Always cite your sources using the citation IDs like [1], [2], etc.
3. If the context doesn't contain enough information, say so explicitly — do not guess.
4. If a question touches on data outside your context, acknowledge the gap rather than filling it.
5. Keep answers professional, clear, and structured.
6. When citing multiple sources, synthesize them coherently.
7. For numerical data, quote exactly as given in the source.{redaction_notice}

Current User Context:
- Name: {user.name}
- Department: {user.department}
- Access Role: {user.role}
- Query Type: {route_label}"""

        user_message = f"""QUESTION: {query}

AVAILABLE CONTEXT:
{context_text}

Please provide a comprehensive, grounded answer based solely on the above context.
Cite relevant sources with their reference numbers [1], [2], etc.
Be specific and use exact figures/data from the sources where available."""

        response = self.client.chat.completions.create(
            model=self.MODEL,
            max_tokens=1200,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
        )

        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        confidence = self._compute_confidence(retrieval_results, answer)
        confidence_label = self._confidence_label(confidence)

        return RAGResponse(
            answer=answer,
            citations=citations,
            sources_used=seen_sources,
            confidence=confidence,
            confidence_label=confidence_label,
            route_label=route_label,
            route_explanation=route_explanation,
            retrieval_results=retrieval_results,
            query=query,
            user=user,
            timestamp=timestamp,
            tokens_used=tokens_used,
        )

    def _compute_confidence(self, results: list, answer: str) -> float:
        if not results:
            return 0.0
        top_scores = [r.score for r in results[:4]]
        avg_score = sum(top_scores) / len(top_scores)
        unique_sources = len(set(r.chunk.source_name for r in results[:6]))
        source_boost = min(unique_sources * 0.03, 0.12)
        hedging = ["i'm not sure", "i cannot find", "not available", "not provided",
                   "unclear", "insufficient", "no information"]
        hedge_penalty = sum(0.08 for h in hedging if h in answer.lower())
        return round(min(0.97, max(0.15, avg_score + source_boost - hedge_penalty)), 3)

    def _confidence_label(self, score: float) -> str:
        if score >= 0.80: return "High"
        if score >= 0.60: return "Medium"
        if score >= 0.40: return "Low"
        return "Very Low"

    def get_confidence_color(self, label: str) -> str:
        return {
            "High": "#00C853", "Medium": "#FFB300",
            "Low": "#FF6D00",  "Very Low": "#D50000", "No Data": "#9E9E9E",
        }.get(label, "#9E9E9E")
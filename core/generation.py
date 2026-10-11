"""
RAG Generation Engine
Calls the Groq API with retrieved context to generate grounded,
cited, hallucination-minimized responses with confidence indicators.
"""

import os
import re
from datetime import datetime
from typing import Optional

import groq
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

from core.retrieval import RetrievalResult  # noqa: E402,F401
from core.rbac import User  # noqa: E402,F401


# ─── RESPONSE MODEL ───────────────────────────────────────────────────────────

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


# ─── GENERATION ENGINE ────────────────────────────────────────────────────────

class GenerationEngine:
    # llama-3.3-70b-versatile was shut down by Groq on 2026-08-16.
    # Override with GROQ_MODEL in .env; if it is missing/retired we fall through this list.
    DEFAULT_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set. "
                "Create a key at https://console.groq.com/keys and add it to your .env file."
            )
        preferred = os.getenv("GROQ_MODEL", "").strip()
        self.models = ([preferred] if preferred else []) + [
            m for m in self.DEFAULT_MODELS if m != preferred
        ]
        self.model = self.models[0]
        # The SDK already retries 429/5xx with backoff; max_retries raises that budget
        self.client = Groq(api_key=api_key, max_retries=3, timeout=45.0)

    # ── main entry point ──────────────────────────────────────────────────────

    def generate(
        self,
        query: str,
        retrieval_results: list,
        user,
        route_label: str,
        route_explanation: str,
        redacted_fields: Optional[list] = None,
    ) -> RAGResponse:
        redacted_fields = redacted_fields or []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not retrieval_results:
            return self._empty_response(
                answer=(
                    "I couldn't find relevant information for your query in the sources you have "
                    "access to. This may be because the information is restricted for your role, "
                    "or doesn't exist in the knowledge base."
                ),
                label="No Data",
                query=query, user=user, timestamp=timestamp,
                route_label=route_label, route_explanation=route_explanation,
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
            redaction_notice = (
                f"\n\nNOTE: The following fields are redacted for this user's role: "
                f"{', '.join(redacted_fields)}. Do not include specific values for these in your response."
            )

        system_prompt = f"""You are an Enterprise AI Assistant for ACME Corporation — a secure, intelligent RAG system.

Your role is to answer employee questions using ONLY the provided source context. You are grounded, precise, and transparent.

STRICT RULES:
1. ONLY use information from the provided context sections. Never hallucinate or infer beyond the context.
2. Always cite your sources using the citation IDs like [1], [2], etc. Only use IDs that appear in the context.
3. If the context doesn't contain enough information, say so explicitly — do not guess.
4. If a question touches on data outside your context, acknowledge the gap rather than filling it.
5. Keep answers professional, clear, and structured (short paragraphs or bullet points; Markdown is fine).
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

        try:
            response = self._complete([
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ])
        except groq.RateLimitError:
            return self._empty_response(
                answer="The Groq API rate limit was reached. Wait a few seconds and ask again "
                       "(free-tier limits are per minute and per day).",
                label="Error", query=query, user=user, timestamp=timestamp,
                route_label=route_label, route_explanation=route_explanation,
                retrieval_results=retrieval_results,
            )
        except groq.AuthenticationError:
            return self._empty_response(
                answer="Groq rejected the API key. Check GROQ_API_KEY in your .env file.",
                label="Error", query=query, user=user, timestamp=timestamp,
                route_label=route_label, route_explanation=route_explanation,
                retrieval_results=retrieval_results,
            )
        except groq.APIConnectionError:
            return self._empty_response(
                answer="Couldn't reach the Groq API. Check your internet connection and try again.",
                label="Error", query=query, user=user, timestamp=timestamp,
                route_label=route_label, route_explanation=route_explanation,
                retrieval_results=retrieval_results,
            )
        except groq.APIStatusError as e:
            return self._empty_response(
                answer=f"Groq returned an error ({e.status_code}) for model '{self.model}'. "
                       f"Set GROQ_MODEL in .env to a current model from console.groq.com/docs/models.",
                label="Error", query=query, user=user, timestamp=timestamp,
                route_label=route_label, route_explanation=route_explanation,
                retrieval_results=retrieval_results,
            )

        answer = response.choices[0].message.content or ""
        answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()
        tokens_used = response.usage.total_tokens if response.usage else 0

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

    # ── helpers ───────────────────────────────────────────────────────────────

    def _complete(self, messages: list):
        """Call Groq, falling through the model list if a model has been retired."""
        last_err = None
        for model in list(self.models):
            kwargs = dict(
                model=model,
                temperature=0.1,               # low temperature = fewer invented details
                max_completion_tokens=2500,    # reasoning models spend part of this on thinking
                messages=messages,
            )
            if model.startswith("openai/gpt-oss"):
                kwargs["reasoning_effort"] = "low"   # keep latency down for RAG answers
            try:
                response = self.client.chat.completions.create(**kwargs)
                self.model = model             # remember the one that worked
                return response
            except groq.NotFoundError as e:
                last_err = e
            except groq.BadRequestError as e:
                if "decommission" in str(e).lower() or "model" in str(e).lower():
                    last_err = e
                else:
                    raise
        raise last_err

    def _empty_response(self, answer, label, query, user, timestamp,
                        route_label, route_explanation, retrieval_results=None) -> RAGResponse:
        return RAGResponse(
            answer=answer,
            citations=[],
            sources_used=[],
            confidence=0.0,
            confidence_label=label,
            route_label=route_label,
            route_explanation=route_explanation,
            retrieval_results=retrieval_results or [],
            query=query,
            user=user,
            timestamp=timestamp,
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
            "Low": "#FF6D00",  "Very Low": "#D50000",
            "No Data": "#9E9E9E", "Error": "#D50000",
        }.get(label, "#9E9E9E")
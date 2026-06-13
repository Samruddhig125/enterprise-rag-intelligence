"""
Enterprise RAG Intelligence System
ACME Corporation Internal AI Assistant

"""

import os
import sys
import time
import streamlit as st

# ─── PAGE CONFIG (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="ACME Enterprise RAG",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.pipeline import EnterprisePipeline

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Global */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1117 0%, #1a1d2e 100%);
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

/* Header banner */
.rag-header {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 50%, #1e1b4b 100%);
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 28px;
    border: 1px solid rgba(99, 102, 241, 0.3);
    position: relative;
    overflow: hidden;
}
.rag-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at top right, rgba(99,102,241,0.15) 0%, transparent 60%);
    pointer-events: none;
}
.rag-header h1 {
    color: #f8fafc;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0 0 6px 0;
    letter-spacing: -0.5px;
}
.rag-header p {
    color: #94a3b8;
    font-size: 0.9rem;
    margin: 0;
}
.rag-header .status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #22c55e;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* Role badge */
.role-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* Response card */
.response-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px 28px;
    margin: 16px 0;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.response-answer {
    font-size: 0.95rem;
    line-height: 1.7;
    color: #1e293b;
}

/* Confidence meter */
.confidence-bar-wrap {
    background: #f1f5f9;
    border-radius: 8px;
    height: 8px;
    overflow: hidden;
    margin-top: 6px;
}
.confidence-bar {
    height: 100%;
    border-radius: 8px;
    transition: width 0.5s ease;
}

/* Citation pill */
.citation-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 4px 4px 4px 0;
    border: 1px solid #e2e8f0;
    background: #f8fafc;
    color: #334155;
}

/* Route badge */
.route-badge {
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    color: #0369a1;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
}

/* Metric card */
.metric-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #1e293b;
}
.metric-label {
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 2px;
}

/* Source type icon badges */
.src-type-pdf   { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.src-type-csv   { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
.src-type-json  { background: #fefce8; color: #ca8a04; border: 1px solid #fde68a; }
.src-type-report{ background: #f0f9ff; color: #0284c7; border: 1px solid #bae6fd; }

/* Access denied */
.access-denied {
    background: #fff1f2;
    border: 1px solid #fecaca;
    border-radius: 12px;
    padding: 20px 24px;
    color: #991b1b;
}

/* Chat history item */
.chat-item {
    padding: 12px 16px;
    border-radius: 8px;
    margin: 6px 0;
    cursor: pointer;
    border: 1px solid #e2e8f0;
    font-size: 0.82rem;
}
.chat-item:hover {
    background: #f1f5f9;
}

/* Suggested query chip */
.query-chip {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 0.8rem;
    color: #334155;
    cursor: pointer;
    display: inline-block;
    margin: 4px;
    transition: all 0.2s;
}
.query-chip:hover {
    background: #e2e8f0;
    border-color: #94a3b8;
}
</style>
""", unsafe_allow_html=True)


# ─── PIPELINE INITIALIZATION ─────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_pipeline():
    pipeline = EnterprisePipeline(data_dir="data")
    return pipeline


@st.cache_data(show_spinner=False)
def initialize_index(_pipeline):
    return _pipeline.initialize()


# ─── SESSION STATE ────────────────────────────────────────────────────────────

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_user" not in st.session_state:
    st.session_state.current_user = "sarah.mitchell"
if "index_info" not in st.session_state:
    st.session_state.index_info = None
if "pending_query" not in st.session_state:
    st.session_state.pending_query = ""


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🔐 ACME RAG System")
    st.markdown("---")

    # Initialize system
    if st.session_state.index_info is None:
        with st.spinner("Initializing knowledge base..."):
            try:
                pipeline = get_pipeline()
                index_info = initialize_index(pipeline)
                st.session_state.index_info = index_info
            except Exception as e:
                st.error(f"Init error: {e}")
                st.stop()
    else:
        pipeline = get_pipeline()

    info = st.session_state.index_info
    if info:
        status_icon = "✅" if info["status"] in ["indexed", "loaded"] else "⚠️"
        st.markdown(f"**{status_icon} Knowledge Base**")
        st.markdown(f"- {info['chunk_count']} indexed chunks")

        stats = info.get("source_stats", {})
        for stype, sdata in stats.items():
            icon = {"pdf": "📄", "csv": "📊", "json": "📋", "report": "📑"}.get(stype, "📁")
            st.markdown(f"- {icon} {sdata['unique_sources']} {stype.upper()} source(s)")

    st.markdown("---")

    # User selector
    st.markdown("### 👤 Active User")
    user_list = pipeline.get_user_list()
    user_options = {f"{u['name']} ({u['role']})": u["username"] for u in user_list}

    default_label = next(
        (label for label, uname in user_options.items() if uname == st.session_state.current_user),
        list(user_options.keys())[0]
    )

    selected_label = st.selectbox(
        "Login as:",
        options=list(user_options.keys()),
        index=list(user_options.keys()).index(default_label),
        label_visibility="collapsed",
    )
    st.session_state.current_user = user_options[selected_label]

    # Show current user card
    current_user_data = next(u for u in user_list if u["username"] == st.session_state.current_user)
    role = current_user_data["role"]
    role_colors = {
        "executive": "#FFD700", "finance": "#4CAF50", "hr": "#2196F3",
        "it_security": "#F44336", "operations": "#FF9800", "employee": "#9E9E9E"
    }
    rc = role_colors.get(role, "#9E9E9E")

    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.05); border-radius:10px; padding:12px; margin-top:8px; border:1px solid rgba(255,255,255,0.1);">
        <div style="font-size:0.8rem; color:#94a3b8; margin-bottom:4px;">Logged in as</div>
        <div style="font-weight:600; font-size:0.95rem;">{current_user_data['name']}</div>
        <div style="font-size:0.78rem; color:#94a3b8; margin-top:2px;">{current_user_data['dept']}</div>
        <div style="margin-top:8px;">
            <span style="background:{rc}22; color:{rc}; border:1px solid {rc}44; padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">
                {role}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Permitted sources
    role_cfg = pipeline.rbac.get_role_config(role)
    permitted = role_cfg["allowed_sources"]
    st.markdown("### 🗂️ Your Data Access")
    if "*" in permitted:
        st.markdown("✅ Full access — all sources")
    else:
        for src in permitted:
            st.markdown(f"✅ {src.replace('_', ' ')}")
        denied = role_cfg["denied_sources"]
        for src in denied[:3]:
            st.markdown(f"🚫 ~~{src.replace('_', ' ')}~~")

    st.markdown("---")

    # Reindex button
    if st.button("🔄 Reindex Knowledge Base", use_container_width=True):
        with st.spinner("Rebuilding index..."):
            idx = pipeline.initialize(force_reindex=True)
            st.session_state.index_info = idx
        st.success("Index rebuilt!")

    # Clear chat
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()


# ─── MAIN CONTENT ─────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="rag-header">
    <h1>🔐 Enterprise RAG Intelligence System</h1>
    <p>
        <span class="status-dot"></span>
        Secure, context-aware AI assistant for ACME Corporation &nbsp;|&nbsp;
        Multi-source retrieval &nbsp;·&nbsp; RBAC enforced &nbsp;·&nbsp; Grounded responses
    </p>
</div>
""", unsafe_allow_html=True)

# Suggested queries based on role
ROLE_QUERIES = {
    "executive": [
        "What was our Q4 2024 revenue and key financial metrics?",
        "Summarize the compliance audit findings for 2024",
        "What security incidents occurred this month?",
        "What is the current system uptime and infrastructure status?",
    ],
    "finance": [
        "What is our Q4 2024 EBITDA and operating cash flow?",
        "Which vendor contracts are expiring soon?",
        "What are the key budget forecasts for Q1 2025?",
        "What is our EMEA revenue exposure and FX risk?",
    ],
    "hr": [
        "What is the leave policy for senior employees?",
        "When are performance reviews conducted?",
        "What is the parental leave policy?",
        "How does the remote work policy work?",
    ],
    "it_security": [
        "What are the critical CVE patching SLAs?",
        "How many security incidents have been logged recently?",
        "What is the MFA and password policy?",
        "Show me recent unauthorized access attempts in the logs",
    ],
    "operations": [
        "What was the system uptime in December 2024?",
        "What incidents occurred in the last month?",
        "What capacity scaling is recommended for Q1?",
        "How many deployments were rolled back in December?",
    ],
    "employee": [
        "What is the annual leave policy?",
        "How does the remote work policy work?",
        "When are bonuses paid?",
        "What is the performance review schedule?",
    ],
}

current_role = current_user_data["role"]
suggestions = ROLE_QUERIES.get(current_role, ROLE_QUERIES["employee"])

st.markdown("**💡 Suggested queries for your role:**")
cols = st.columns(2)
for i, suggestion in enumerate(suggestions):
    with cols[i % 2]:
        if st.button(f"↗ {suggestion[:55]}{'...' if len(suggestion) > 55 else ''}", key=f"sug_{i}", use_container_width=True):
            st.session_state.pending_query = suggestion
            st.rerun()

st.markdown("---")

# Query input
col_q, col_btn = st.columns([5, 1])
with col_q:
    query_input = st.text_input(
        "Ask your question:",
        value=st.session_state.pending_query,
        placeholder="e.g. What is the Q4 revenue breakdown by region?",
        label_visibility="collapsed",
        key="query_input_field",
    )
with col_btn:
    search_clicked = st.button("🔍 Ask", type="primary", use_container_width=True)

# Clear pending query after use
if st.session_state.pending_query and query_input == st.session_state.pending_query:
    st.session_state.pending_query = ""

# Advanced options
with st.expander("⚙️ Advanced Options", expanded=False):
    adv_col1, adv_col2 = st.columns(2)
    with adv_col1:
        top_k = st.slider("Retrieval depth (top-k chunks)", min_value=3, max_value=12, value=6)
    with adv_col2:
        show_chunks = st.checkbox("Show raw retrieved chunks", value=False)
        show_trace = st.checkbox("Show retrieval trace", value=True)


# ─── PROCESS QUERY ────────────────────────────────────────────────────────────

if search_clicked and query_input.strip():
    user_query = query_input.strip()

    with st.spinner("🧠 Retrieving and generating grounded response..."):
        start_time = time.time()

        result = pipeline.query(
            query_text=user_query,
            username=st.session_state.current_user,
            top_k=top_k,
        )

        elapsed = time.time() - start_time

    # ── ACCESS DENIED ──
    if "error" in result:
        st.markdown(f"""
        <div class="access-denied">
            <div style="font-size:1.2rem; margin-bottom:8px;">🚨 Access Denied</div>
            <div>{result['error']}</div>
            <div style="margin-top:12px; font-size:0.82rem; opacity:0.8;">
                Your role <strong>{current_role}</strong> does not have permission to access this information.
                Contact your IT administrator to request elevated access.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Log to chat history
        st.session_state.chat_history.append({
            "query": user_query,
            "response": None,
            "access_denied": True,
            "error": result["error"],
            "user": current_user_data["name"],
            "role": current_role,
        })

    # ── SUCCESSFUL RESPONSE ──
    elif "response" in result:
        rag = result["response"]
        conf_color = pipeline.generator.get_confidence_color(rag.confidence_label)

        # Top metrics row
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{len(rag.retrieval_results)}</div>
                <div class="metric-label">Chunks Retrieved</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{len(rag.sources_used)}</div>
                <div class="metric-label">Sources Used</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value" style="color:{conf_color};">{rag.confidence_label}</div>
                <div class="metric-label">Confidence</div>
            </div>""", unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{elapsed:.1f}s</div>
                <div class="metric-label">Response Time</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("")

        # Route explanation
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px; flex-wrap:wrap;">
            <span class="route-badge">{rag.route_explanation}</span>
            <span style="font-size:0.8rem; color:#64748b;">
                Query routed to: <strong>{rag.route_label}</strong>
            </span>
            <span style="font-size:0.8rem; color:#64748b;">
                {rag.tokens_used} tokens used
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Main response
        st.markdown(f"""
        <div class="response-card">
            <div style="font-size:0.75rem; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:12px; font-weight:600;">
                AI Response
            </div>
            <div class="response-answer">{rag.answer.replace(chr(10), '<br>')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Confidence indicator
        conf_pct = int(rag.confidence * 100)
        st.markdown(f"""
        <div style="margin: 8px 0 16px 0;">
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#64748b; margin-bottom:4px;">
                <span>Confidence Score</span>
                <span style="color:{conf_color}; font-weight:600;">{rag.confidence_label} ({conf_pct}%)</span>
            </div>
            <div class="confidence-bar-wrap">
                <div class="confidence-bar" style="width:{conf_pct}%; background:{conf_color};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Citations
        if rag.citations:
            st.markdown("**📎 Source Citations**")
            type_icons = {"pdf": "📄", "csv": "📊", "json": "📋", "report": "📑"}
            type_classes = {"pdf": "src-type-pdf", "csv": "src-type-csv", "json": "src-type-json", "report": "src-type-report"}

            citation_html = ""
            for cit in rag.citations:
                icon = type_icons.get(cit["type"], "📁")
                cls = type_classes.get(cit["type"], "")
                score_pct = int(cit["relevance_score"] * 100)
                classification_badge = ""
                if cit["classification"] == "CONFIDENTIAL":
                    classification_badge = ' <span style="color:#dc2626; font-size:0.7rem;">🔒 CONF</span>'

                citation_html += f"""
                <span class="citation-pill {cls}">
                    <strong>{cit['id']}</strong>
                    {icon} {cit['source']}
                    · {cit['section']}
                    · {score_pct}% match
                    {classification_badge}
                </span>"""

            st.markdown(citation_html, unsafe_allow_html=True)

        # Retrieval trace
        if show_trace and rag.retrieval_results:
            with st.expander(f"🔍 Retrieval Trace ({len(rag.retrieval_results)} chunks)", expanded=False):
                for i, r in enumerate(rag.retrieval_results):
                    chunk = r.chunk
                    icon = type_icons.get(chunk.source_type, "📁")
                    rel_color = {"High": "#00C853", "Medium": "#FFB300", "Low": "#FF6D00"}.get(r.relevance_label, "#9E9E9E")

                    st.markdown(f"""
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px 16px; margin:6px 0;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <span style="font-weight:600; font-size:0.85rem;">
                                [{i+1}] {icon} {chunk.source_name}
                                <span style="color:#64748b; font-weight:400;"> · {chunk.page_or_row}</span>
                            </span>
                            <span style="color:{rel_color}; font-size:0.8rem; font-weight:600;">
                                {r.relevance_label} ({int(r.score*100)}%)
                            </span>
                        </div>
                        <div style="font-size:0.75rem; color:#64748b; margin-bottom:4px;">
                            {chunk.department} | {chunk.classification} | {chunk.source_type.upper()}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if show_chunks:
                        with st.expander(f"Raw content [{i+1}]"):
                            st.code(chunk.content[:800] + ("..." if len(chunk.content) > 800 else ""), language=None)

        # Save to history
        st.session_state.chat_history.append({
            "query": user_query,
            "response": rag.answer,
            "confidence": rag.confidence_label,
            "sources": rag.sources_used,
            "access_denied": False,
            "user": current_user_data["name"],
            "role": current_role,
            "timestamp": rag.timestamp,
        })


# ─── CHAT HISTORY ─────────────────────────────────────────────────────────────

if st.session_state.chat_history:
    st.markdown("---")
    st.markdown("### 📜 Session History")

    for i, item in enumerate(reversed(st.session_state.chat_history)):
        if item.get("access_denied"):
            st.markdown(f"""
            <div class="chat-item" style="border-left:3px solid #dc2626;">
                <div style="font-size:0.75rem; color:#64748b;">{item['user']} ({item['role']})</div>
                <div style="font-weight:500;">🚫 {item['query']}</div>
                <div style="font-size:0.75rem; color:#dc2626; margin-top:2px;">Access denied</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            conf_color_hist = {"High": "#00C853", "Medium": "#FFB300", "Low": "#FF6D00", "Very Low": "#D50000"}.get(item.get("confidence", ""), "#9E9E9E")
            sources_str = ", ".join(item.get("sources", []))[:80]
            st.markdown(f"""
            <div class="chat-item" style="border-left:3px solid {conf_color_hist};">
                <div style="font-size:0.75rem; color:#64748b; display:flex; justify-content:space-between;">
                    <span>{item['user']} ({item['role']})</span>
                    <span style="color:{conf_color_hist}; font-weight:600;">{item.get('confidence','')} confidence</span>
                </div>
                <div style="font-weight:500; margin: 3px 0;">❓ {item['query']}</div>
                <div style="font-size:0.75rem; color:#64748b;">Sources: {sources_str}</div>
            </div>
            """, unsafe_allow_html=True)

# ─── FOOTER ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#94a3b8; font-size:0.78rem; padding:12px 0;">
    ACME Enterprise RAG Intelligence System &nbsp;·&nbsp;
    All responses grounded in enterprise data &nbsp;·&nbsp; RBAC enforced
</div>
""", unsafe_allow_html=True)
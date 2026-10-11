"""
ACME Enterprise RAG — Intelligence System
Secure, role-aware AI assistant. Streamlit UI.
"""

import html
import os
import re
import sys
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

# Some Linux hosts (e.g. Streamlit Community Cloud) ship an sqlite3 too old for ChromaDB.
# pysqlite3-binary (installed on Linux only, see requirements.txt) replaces it when present.
try:
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass

# On a fresh deployment, build the demo dataset if the data/ folder wasn't committed.
if not os.path.exists(os.path.join("data", "rbac_policy.json")) and os.path.exists("generate_data.py"):
    import subprocess
    subprocess.run([sys.executable, "generate_data.py"], check=True)

import streamlit as st

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ACME Enterprise RAG",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.pipeline import EnterprisePipeline  # noqa: E402


# ─── THEME DATA ───────────────────────────────────────────────────────────────

ROLE_COLORS = {
    "executive": "#C9A24B", "finance": "#2F9E74", "hr": "#4A86C5",
    "it_security": "#D2584D", "operations": "#D98A3D", "employee": "#8A97A3",
}
CONF_COLORS = {
    "High": "#1F8A5F", "Medium": "#C98A12", "Low": "#D2661F",
    "Very Low": "#B3261E", "No Data": "#7C8794", "Error": "#B3261E",
}
REL_COLORS = {"High": "#1F8A5F", "Medium": "#C98A12", "Low": "#D2661F"}
TYPE_TAGS = {
    "pdf": ("PDF", "t-pdf"), "csv": ("CSV", "t-csv"),
    "json": ("LOG", "t-json"), "report": ("REPORT", "t-report"),
}
KB_LABELS = {
    "pdf": "Policy documents", "csv": "Data tables",
    "json": "Event logs", "report": "Reports",
}
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

esc = html.escape


# ─── STYLES ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Public+Sans:wght@400;500;600&display=swap');

:root {
  --ink:#14212B; --steel:#1E3341; --brass:#B88A3E; --brass-d:#8F6A2A; --brass-soft:#F4ECD8;
  --paper:#F3F5F4; --card:#FFFFFF; --line:#DCE2E5; --text:#17242D; --muted:#5F7380;
  --ok:#1F8A5F; --warn:#C98A12; --risk:#B3261E;
}

.stApp { background: var(--paper); font-family:'Public Sans', system-ui, sans-serif; color: var(--text); }
h1, h2, h3, h4 { font-family:'Sora', 'Public Sans', sans-serif; letter-spacing:-0.01em; color: var(--text); }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1000px; padding-top: 1.6rem; padding-bottom: 7rem; }
:focus-visible { outline: 2px solid var(--brass-d) !important; outline-offset: 2px; }

/* Pin colours so the app looks right even if Streamlit is in dark mode */
.stApp { color-scheme: light; }
[data-testid="stChatMessage"] :is(p, li, h1, h2, h3, h4, strong, em, td, th) { color: var(--text); }
[data-testid="stChatMessage"] [data-testid="stExpander"] { background:#fff; border:1px solid var(--line); border-radius:12px; }
[data-testid="stChatMessage"] [data-testid="stExpander"] summary * { color: var(--text) !important; }
/* Markdown tables, quotes and inline code inside answers */
[data-testid="stChatMessage"] :is(table, thead, tbody, tr, td, th, td *, th *) {
  color: var(--text) !important; -webkit-text-fill-color: var(--text) !important; opacity: 1 !important;
}
[data-testid="stChatMessage"] table { border-collapse: collapse; width: 100%; font-size: .9rem; margin: .5rem 0 .8rem 0; }
[data-testid="stChatMessage"] :is(td, th) { background: #fff !important; border: 1px solid var(--line) !important; padding: .5rem .7rem !important; vertical-align: top; }
[data-testid="stChatMessage"] th { background: #EDF1F3 !important; font-weight: 600; text-align: left; }
[data-testid="stChatMessage"] blockquote { color: var(--muted) !important; border-left: 3px solid var(--brass); }
[data-testid="stChatMessage"] :not(pre) > code { background: #EDF1F3; color: #3B2F12 !important; border-radius: 4px; padding: 1px 5px; }
[data-testid="stBottom"], [data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] { background: var(--paper) !important; }
[data-testid="stChatInput"] > div { background:#fff !important; border:1px solid var(--line) !important; border-radius:14px; }
[data-testid="stChatInput"] textarea { color: var(--text) !important; -webkit-text-fill-color: var(--text) !important; background:#fff !important; }
[data-testid="stChatInput"] textarea::placeholder { color:#7F909B !important; -webkit-text-fill-color:#7F909B !important; }

/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] { background: var(--ink); border-right: 1px solid #0B151C; }
[data-testid="stSidebar"] :is(p, li, label, h1, h2, h3, h4) { color: #D5DFE5; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.16); border-radius: 10px;
}
[data-testid="stSidebar"] [data-baseweb="select"] * { color: #E8EEF2 !important; }
[data-testid="stSidebar"] [data-baseweb="select"] svg { fill: #E8EEF2; }
[data-testid="stSidebar"] .stButton > button {
  background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.16);
  border-radius: 10px; color: #E8EEF2; transition: border-color .15s, background .15s;
}
[data-testid="stSidebar"] .stButton > button:hover { border-color: var(--brass); background: rgba(184,138,62,.14); }
[data-testid="stSidebar"] [data-testid="stExpander"] {
  border: 1px solid rgba(255,255,255,.12); border-radius: 10px; background: transparent;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary { color: #D5DFE5; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.1); }

.vq-brand { display:flex; align-items:center; gap:12px; padding: 4px 0 14px 0; }
.vq-brand-name { font-family:'Sora',sans-serif; font-weight:700; font-size:1.12rem; color:#fff; line-height:1.15; }
.vq-brand-sub { font-size:.74rem; color:#8FA3B0; margin-top:2px; }
.vq-sec { font-size:.78rem; font-weight:600; color:#8FA3B0; margin: 14px 0 6px 0; }

.vq-kb { background: rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.1); border-radius:10px; padding:10px 12px; }
.vq-kb-head { display:flex; align-items:center; gap:8px; font-size:.84rem; font-weight:600; color:#fff; }
.vq-dot { width:8px; height:8px; border-radius:50%; background:#3DD598; box-shadow:0 0 0 0 rgba(61,213,152,.6); animation: vqpulse 2.4s infinite; flex:none; }
@keyframes vqpulse { 0%{box-shadow:0 0 0 0 rgba(61,213,152,.55)} 70%{box-shadow:0 0 0 7px rgba(61,213,152,0)} 100%{box-shadow:0 0 0 0 rgba(61,213,152,0)} }
@media (prefers-reduced-motion: reduce) { .vq-dot { animation:none; } }
.vq-kb-row { display:flex; justify-content:space-between; font-size:.78rem; color:#9FB2BE; margin-top:5px; }

.vq-user { background: rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.12); border-radius:10px; padding:11px 12px; margin-top:8px; }
.vq-user-name { font-weight:600; font-size:.95rem; color:#fff; }
.vq-user-dept { font-size:.78rem; color:#8FA3B0; margin-top:1px; }
.vq-role { display:inline-block; margin-top:8px; padding:2px 10px; border-radius:20px; font-size:.74rem; font-weight:600; border:1px solid; }

.vq-ledger { margin-top:2px; }
.vq-door { display:flex; align-items:center; gap:9px; font-size:.82rem; padding:4px 0; color:#D5DFE5; }
.vq-door .ic { width:16px; height:16px; border-radius:4px; display:inline-flex; align-items:center; justify-content:center; font-size:.68rem; font-weight:700; flex:none; }
.vq-door.open .ic { background: rgba(61,213,152,.18); color:#3DD598; }
.vq-door.shut { color:#7F93A0; text-decoration: line-through; text-decoration-color: rgba(127,147,160,.5); }
.vq-door.shut .ic { background: rgba(240,106,95,.16); color:#F06A5F; text-decoration:none; }
.vq-foot { font-size:.72rem; color:#6F8492; margin-top:18px; line-height:1.5; }

/* ── Top bar & welcome ───────────────────────────────────── */
.vq-topbar { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;
  padding-bottom:12px; border-bottom:1px solid var(--line); margin-bottom:18px; }
.vq-topbar-title { font-family:'Sora',sans-serif; font-weight:600; font-size:.98rem; display:flex; align-items:center; gap:9px; }
.vq-chip { display:inline-flex; align-items:center; gap:6px; padding:3px 11px; border-radius:20px; font-size:.78rem;
  border:1px solid var(--line); background:#fff; color:var(--muted); }
.vq-chip b { color: var(--text); font-weight:600; }
.vq-chip.route { background:#EEF5F3; border-color:#CFE3DD; color:#24594B; font-weight:500; }

.vq-hero { padding: 18px 0 8px 0; }
.vq-hero h1 { font-size: 2.05rem; line-height:1.18; margin:0 0 10px 0; max-width: 18em; }
.vq-hero p { font-size: 1rem; color: var(--muted); max-width: 40em; margin:0; line-height:1.6; }
.vq-h { font-family:'Sora',sans-serif; font-weight:600; font-size:.95rem; margin: 26px 0 10px 0; }

.vq-flow { display:grid; grid-template-columns: repeat(4, 1fr); gap:0; margin-top:6px; border:1px solid var(--line); border-radius:14px; background:#fff; overflow:hidden; }
.vq-step { padding:14px 16px; border-right:1px solid var(--line); }
.vq-step:last-child { border-right:none; }
.vq-step-n { width:22px; height:22px; border-radius:50%; background: var(--ink); color:#fff; font-size:.72rem; font-weight:600; display:inline-flex; align-items:center; justify-content:center; }
.vq-step-t { font-weight:600; font-size:.9rem; margin:8px 0 3px 0; }
.vq-step-d { font-size:.78rem; color:var(--muted); line-height:1.5; }
@media (max-width: 760px) { .vq-flow { grid-template-columns: 1fr 1fr; } .vq-step:nth-child(2) { border-right:none; } .vq-step:nth-child(-n+2) { border-bottom:1px solid var(--line);} }

/* Suggestion buttons (main area only) */
[data-testid="stMain"] .stButton > button, section.main .stButton > button {
  width:100%; min-height:4.1rem; text-align:left; justify-content:flex-start;
  background:#fff; border:1px solid var(--line); border-radius:12px; padding:.8rem 1rem; color:var(--text);
  box-shadow:none; transition: border-color .15s, background .15s;
}
[data-testid="stMain"] .stButton > button p, section.main .stButton > button p { text-align:left; font-size:.92rem; line-height:1.4; color: var(--text) !important; }
[data-testid="stMain"] .stButton > button:hover, section.main .stButton > button:hover { border-color: var(--brass); background:#FCF9F1; color:var(--text); }

/* ── Chat ────────────────────────────────────────────────── */
[data-testid="stChatMessage"] { background:#fff; border:1px solid var(--line); border-radius:14px; padding: 1rem 1.25rem; margin-bottom:.9rem; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: var(--brass-soft); border:none; border-left:3px solid var(--brass); border-radius: 4px 14px 14px 4px;
}
[data-testid="stChatMessage"] p { line-height:1.65; color: var(--text); }
.vq-asker { font-size:.76rem; color: var(--brass-d); margin-bottom:2px; font-weight:600; }
[data-testid="stChatInput"] { border-radius: 14px; }


/* ── Answer body: our own HTML, colours pinned regardless of theme ── */
.vq-answer { font-size:.95rem; line-height:1.65; overflow-x:auto; }
.vq-answer, .vq-answer * { color: var(--text) !important; -webkit-text-fill-color: var(--text) !important; opacity: 1 !important; }
.vq-answer p { margin: .2rem 0 .75rem 0; }
.vq-answer h1, .vq-answer h2, .vq-answer h3, .vq-answer h4 { font-family:'Sora',sans-serif; font-size:1.02rem; margin: 1rem 0 .45rem 0; }
.vq-answer ul, .vq-answer ol { padding-left: 1.3rem; margin: .2rem 0 .75rem 0; }
.vq-answer table { border-collapse: collapse; width: 100%; font-size:.9rem; margin: .4rem 0 .9rem 0; }
.vq-answer th, .vq-answer td { border:1px solid var(--line); padding:.45rem .65rem; text-align:left; vertical-align:top; background:#fff; }
.vq-answer th { background:#EDF1F3; font-weight:600; }
.vq-answer code { background:#EDF1F3; padding:1px 5px; border-radius:4px; font-size:.86em; }
.vq-answer pre { background:#F3F5F4; padding:10px 12px; border-radius:8px; overflow-x:auto; }
.vq-answer pre code { background:transparent; padding:0; }
.vq-answer blockquote { margin:.4rem 0 .8rem 0; padding-left:12px; border-left:3px solid var(--brass); }
.vq-answer a { color: var(--brass-d) !important; -webkit-text-fill-color: var(--brass-d) !important; }

.vq-meta { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px; }

.vq-conf { margin: 14px 0 4px 0; padding-top:12px; border-top:1px dashed var(--line); }
.vq-conf-head { display:flex; justify-content:space-between; font-size:.82rem; color:var(--muted); margin-bottom:6px; }
.vq-conf-head b { font-weight:600; }
.vq-seg { display:grid; grid-template-columns: repeat(10, 1fr); gap:4px; }
.vq-seg span { height:8px; border-radius:2px; background:#E3E8EB; }
.vq-conf-note { font-size:.72rem; color:#8696A2; margin-top:6px; }

.vq-cites-h { font-family:'Sora',sans-serif; font-weight:600; font-size:.86rem; margin: 16px 0 8px 0; }
.vq-cites { display:grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap:8px; }
.vq-cite { display:flex; gap:10px; border:1px solid var(--line); border-radius:10px; padding:9px 11px; background:#FAFBFB; }
.vq-cite-id { font-weight:600; font-size:.8rem; color: var(--brass-d); min-width:22px; }
.vq-cite-name { font-weight:600; font-size:.84rem; line-height:1.3; }
.vq-cite-meta { font-size:.75rem; color:var(--muted); margin-top:3px; display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
.vq-lock { color: var(--risk); font-weight:600; }

.vq-tag { padding:1px 7px; border-radius:5px; font-size:.68rem; font-weight:600; border:1px solid; }
.t-pdf { background:#FDF1F0; color:#B3261E; border-color:#F4CBC7; }
.t-csv { background:#EEF8F3; color:#1F7A55; border-color:#C5E5D6; }
.t-json { background:#FBF5E6; color:#946A0A; border-color:#EBD9A8; }
.t-report { background:#EDF4FB; color:#2F6FA8; border-color:#C6DBEF; }

.vq-trace { border:1px solid var(--line); border-radius:10px; padding:9px 12px; margin:6px 0; background:#FAFBFB; }
.vq-trace-top { display:flex; justify-content:space-between; gap:10px; font-size:.84rem; font-weight:600; }
.vq-trace-sub { font-size:.74rem; color:var(--muted); margin-top:3px; }
.vq-relbar { height:4px; border-radius:2px; background:#E3E8EB; margin-top:7px; overflow:hidden; }
.vq-relbar i { display:block; height:100%; border-radius:2px; }

.vq-denied { border:1px solid #F1C7C3; border-left:4px solid var(--risk); background:#FFF6F5; border-radius:10px; padding:14px 16px; }
.vq-denied-t { font-family:'Sora',sans-serif; font-weight:600; color:var(--risk); margin-bottom:4px; }
.vq-denied-b { color:#5C1C17; line-height:1.55; }
.vq-denied-f { font-size:.78rem; color:#8A4A45; margin-top:9px; }
.vq-error { border:1px solid #F1D9A8; border-left:4px solid var(--warn); background:#FFFAEF; border-radius:10px; padding:14px 16px; color:#5B4410; line-height:1.55; }
.vq-error b { font-family:'Sora',sans-serif; }
</style>
""", unsafe_allow_html=True)


# ─── PIPELINE ─────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_pipeline():
    return EnterprisePipeline(data_dir="data")


@st.cache_data(show_spinner=False)
def initialize_index(_pipeline):
    return _pipeline.initialize()


# ─── SESSION STATE ────────────────────────────────────────────────────────────

st.session_state.setdefault("messages", [])
st.session_state.setdefault("current_user", "sarah.mitchell")
st.session_state.setdefault("index_info", None)
st.session_state.setdefault("queued_prompt", None)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def type_tag(stype: str) -> str:
    label, cls = TYPE_TAGS.get(stype, (stype.upper(), "t-report"))
    return f'<span class="vq-tag {cls}">{esc(label)}</span>'


def confidence_meter(conf: float, label: str) -> str:
    color = CONF_COLORS.get(label, "#7C8794")
    filled = max(0, min(10, round(conf * 10)))
    segs = "".join(
        f'<span style="background:{color}"></span>' if i < filled else "<span></span>"
        for i in range(10)
    )
    return f"""
    <div class="vq-conf">
      <div class="vq-conf-head"><span>Confidence</span><b style="color:{color}">{esc(label)} · {int(conf*100)}%</b></div>
      <div class="vq-seg">{segs}</div>
      <div class="vq-conf-note">Estimated from retrieval relevance and source spread. It is not a guarantee the answer is correct.</div>
    </div>"""


def citations_html(citations: list) -> str:
    cards = ""
    for c in citations:
        lock = '<span class="vq-lock">confidential</span>' if c["classification"] == "CONFIDENTIAL" else ""
        cards += f"""
        <div class="vq-cite">
          <div class="vq-cite-id">{esc(c['id'])}</div>
          <div>
            <div class="vq-cite-name">{esc(c['source'])}</div>
            <div class="vq-cite-meta">{type_tag(c['type'])}<span>{esc(c['section'])}</span>
              <span>{int(c['relevance_score']*100)}% match</span>{lock}</div>
          </div>
        </div>"""
    return f'<div class="vq-cites-h">Sources</div><div class="vq-cites">{cards}</div>'


def _inline(t: str) -> str:
    t = esc(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    return t


def _cells(line: str) -> list:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def md_to_html(text: str) -> str:
    """Small, dependency-free Markdown -> HTML (headings, lists, tables, bold/italic/code).
    All text is HTML-escaped first, so model output can never inject tags."""
    lines = text.replace("\r\n", "\n").split("\n")
    out, para, kind = [], [], None

    def close_para():
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para.clear()

    def close_list():
        nonlocal kind
        if kind:
            out.append(f"</{kind}>")
            kind = None

    i = 0
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if not s:
            close_para(); close_list(); i += 1; continue

        # table: header row + separator row
        if (s.startswith("|") and i + 1 < len(lines)
                and "-" in lines[i + 1] and re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", lines[i + 1])):
            close_para(); close_list()
            head = _cells(s)
            i += 2
            body = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                body.append(_cells(lines[i])); i += 1
            h = "".join(f"<th>{_inline(c)}</th>" for c in head)
            b = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in body)
            out.append(f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>")
            continue

        m = re.match(r"^#{1,6}\s+(.*)$", s)
        if m:
            close_para(); close_list(); out.append(f"<h4>{_inline(m.group(1))}</h4>"); i += 1; continue

        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            close_para(); close_list(); out.append("<hr>"); i += 1; continue

        m = re.match(r"^[-*•]\s+(.*)$", s)
        if m:
            close_para()
            if kind != "ul":
                close_list(); out.append("<ul>"); kind = "ul"
            out.append(f"<li>{_inline(m.group(1))}</li>"); i += 1; continue

        m = re.match(r"^\d+[.)]\s+(.*)$", s)
        if m:
            close_para()
            if kind != "ol":
                close_list(); out.append("<ol>"); kind = "ol"
            out.append(f"<li>{_inline(m.group(1))}</li>"); i += 1; continue

        if kind and raw[:1] in (" ", "\t") and out and out[-1].endswith("</li>"):
            out[-1] = out[-1][:-5] + " " + _inline(s) + "</li>"   # wrapped list item
        else:
            close_list(); para.append(s)
        i += 1

    close_para(); close_list()
    return "".join(out)


def render_answer(text: str):
    """Render the answer as our own HTML so colours never depend on the Streamlit theme."""
    st.markdown(f'<div class="vq-answer">{md_to_html(text)}</div>', unsafe_allow_html=True)


def render_user_msg(m: dict):
    with st.chat_message("user", avatar="👤"):
        st.markdown(f'<div class="vq-asker">{esc(m["name"])} · {esc(m["user_role"])}</div>', unsafe_allow_html=True)
        st.markdown(m["content"])


def render_assistant_msg(m: dict, show_trace: bool, show_chunks: bool):
    kind = m["kind"]

    if kind == "denied":
        reason = m["text"].replace("🔒 Access Denied: ", "")
        st.markdown(f"""
        <div class="vq-denied">
          <div class="vq-denied-t">Blocked by access policy</div>
          <div class="vq-denied-b">{esc(reason)}</div>
          <div class="vq-denied-f">Signed in as <b>{esc(m['name'])}</b> ({esc(m['user_role'])}).
          If you need this information, ask your manager or IT administrator for elevated access.</div>
        </div>""", unsafe_allow_html=True)
        return

    if kind == "error":
        st.markdown(f'<div class="vq-error"><b>Something went wrong</b><br>{esc(m["text"])}</div>', unsafe_allow_html=True)
        return

    chips = f'<span class="vq-chip route">{esc(m["route_explanation"])}</span>'
    chips += f'<span class="vq-chip"><b>{m["n_chunks"]}</b> chunks from <b>{m["n_sources"]}</b> sources</span>'
    if m["tokens"]:
        chips += f'<span class="vq-chip"><b>{m["tokens"]:,}</b> tokens</span>'
    chips += f'<span class="vq-chip"><b>{m["elapsed"]:.1f}s</b></span>'
    st.markdown(f'<div class="vq-meta">{chips}</div>', unsafe_allow_html=True)

    render_answer(m["answer"])

    if m["confidence_label"] != "No Data":
        st.markdown(confidence_meter(m["confidence"], m["confidence_label"]), unsafe_allow_html=True)

    if m["citations"]:
        st.markdown(citations_html(m["citations"]), unsafe_allow_html=True)

    if show_trace and m["trace"]:
        with st.expander(f"How this answer was built · retrieval trace ({len(m['trace'])} chunks)"):
            for t in m["trace"]:
                color = REL_COLORS.get(t["label"], "#7C8794")
                pct = int(t["score"] * 100)
                st.markdown(f"""
                <div class="vq-trace">
                  <div class="vq-trace-top">
                    <span>[{t['idx']}] {esc(t['source'])} <span style="font-weight:400;color:var(--muted)">· {esc(t['section'])}</span></span>
                    <span style="color:{color}">{esc(t['label'])} · {pct}%</span>
                  </div>
                  <div class="vq-trace-sub">{type_tag(t['type'])} &nbsp;{esc(t['dept'])} · {esc(t['classification'])}</div>
                  <div class="vq-relbar"><i style="width:{pct}%;background:{color}"></i></div>
                </div>""", unsafe_allow_html=True)
                if show_chunks:
                    st.code(t["content"], language=None)


def run_query(pipeline, text: str, user: dict, top_k: int) -> dict:
    base = {"role": "assistant", "name": user["name"], "user_role": user["role"]}
    start = time.time()
    try:
        result = pipeline.query(query_text=text, username=user["username"], top_k=top_k)
    except Exception as e:  # keep the UI alive on retrieval/model failures
        return {**base, "kind": "error", "text": f"{type(e).__name__}: {e}"}
    elapsed = time.time() - start

    if "error" in result:
        kind = "denied" if result.get("access_denied") else "error"
        return {**base, "kind": kind, "text": result["error"]}

    rag = result["response"]
    if rag.confidence_label == "Error":
        return {**base, "kind": "error", "text": rag.answer}

    trace = [{
        "idx": i + 1,
        "source": r.chunk.source_name, "section": r.chunk.page_or_row,
        "type": r.chunk.source_type, "dept": r.chunk.department,
        "classification": r.chunk.classification,
        "score": r.score, "label": r.relevance_label,
        "content": r.chunk.content[:900] + ("…" if len(r.chunk.content) > 900 else ""),
    } for i, r in enumerate(rag.retrieval_results)]

    return {
        **base, "kind": "answer",
        "answer": rag.answer, "confidence": rag.confidence,
        "confidence_label": rag.confidence_label,
        "route_label": rag.route_label, "route_explanation": rag.route_explanation,
        "tokens": rag.tokens_used, "elapsed": elapsed,
        "citations": rag.citations, "trace": trace,
        "n_chunks": len(rag.retrieval_results), "n_sources": len(rag.sources_used),
    }


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="vq-brand">
      <svg width="36" height="36" viewBox="0 0 34 34" fill="none" aria-hidden="true">
        <path d="M17 3 L29 7.5 V16.5 C29 23.2 24 28.6 17 31 C10 28.6 5 23.2 5 16.5 V7.5 Z"
              stroke="#B88A3E" stroke-width="2" fill="rgba(184,138,62,.14)"/>
        <circle cx="17" cy="14.5" r="3.2" fill="#B88A3E"/>
        <path d="M15.6 16.5 H18.4 L19.2 23 H14.8 Z" fill="#B88A3E"/>
      </svg>
      <div>
        <div class="vq-brand-name">ACME Enterprise RAG</div>
        <div class="vq-brand-sub">Role-aware answers, with receipts</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Initialise knowledge base
    if st.session_state.index_info is None:
        with st.spinner("Initializing knowledge base…"):
            try:
                pipeline = get_pipeline()
                st.session_state.index_info = initialize_index(pipeline)
            except Exception as e:
                st.error(f"Init error: {e}")
                st.stop()
    else:
        pipeline = get_pipeline()

    info = st.session_state.index_info or {}
    ready = info.get("status") in ("indexed", "loaded")
    rows = "".join(
        f'<div class="vq-kb-row"><span>{esc(KB_LABELS.get(t, t.upper()))}</span><span>{d["unique_sources"]} source(s)</span></div>'
        for t, d in info.get("source_stats", {}).items()
    )
    st.markdown(f"""
    <div class="vq-sec">Knowledge base</div>
    <div class="vq-kb">
      <div class="vq-kb-head"><span class="vq-dot"></span>{'Ready' if ready else 'Check index'} · {info.get('chunk_count', 0)} chunks</div>
      {rows}
    </div>""", unsafe_allow_html=True)

    # User switcher
    st.markdown('<div class="vq-sec">Signed in as</div>', unsafe_allow_html=True)
    user_list = pipeline.get_user_list()
    labels = [f"{u['name']} ({u['role']})" for u in user_list]
    usernames = [u["username"] for u in user_list]
    idx = usernames.index(st.session_state.current_user) if st.session_state.current_user in usernames else 0
    chosen = st.selectbox("Sign in as", labels, index=idx, label_visibility="collapsed")
    st.session_state.current_user = usernames[labels.index(chosen)]

    current_user = next(u for u in user_list if u["username"] == st.session_state.current_user)
    role = current_user["role"]
    rc = ROLE_COLORS.get(role, "#8A97A3")
    st.markdown(f"""
    <div class="vq-user">
      <div class="vq-user-name">{esc(current_user['name'])}</div>
      <div class="vq-user-dept">{esc(current_user['dept'])}</div>
      <span class="vq-role" style="color:{rc};border-color:{rc}66;background:{rc}1F">{esc(role.replace('_', ' '))}</span>
    </div>""", unsafe_allow_html=True)

    # Clearance ledger
    role_cfg = pipeline.rbac.get_role_config(role)
    permitted = role_cfg["allowed_sources"]
    denied = role_cfg["denied_sources"]
    st.markdown('<div class="vq-sec">What you can open</div>', unsafe_allow_html=True)
    if "*" in permitted:
        doors = '<div class="vq-door open"><span class="ic">✓</span>All sources · full clearance</div>'
    else:
        doors = "".join(
            f'<div class="vq-door open"><span class="ic">✓</span>{esc(s.replace("_", " "))}</div>' for s in permitted
        ) + "".join(
            f'<div class="vq-door shut"><span class="ic">✕</span>{esc(s.replace("_", " "))}</div>' for s in denied
        )
    st.markdown(f'<div class="vq-ledger">{doors}</div>', unsafe_allow_html=True)

    # Settings
    st.markdown('<div class="vq-sec">Settings</div>', unsafe_allow_html=True)
    with st.expander("Retrieval & display", expanded=False):
        top_k = st.slider("Chunks to retrieve (top-k)", 3, 12, 6)
        show_trace = st.checkbox("Show retrieval trace", value=True)
        show_chunks = st.checkbox("Include raw chunk text in trace", value=False)

    if st.button("Reindex knowledge base", use_container_width=True):
        with st.spinner("Rebuilding index…"):
            st.session_state.index_info = pipeline.initialize(force_reindex=True)
        st.rerun()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    model_name = getattr(pipeline.generator, "model", "LLM")
    st.markdown(
        f'<div class="vq-foot">{esc(model_name)} on Groq · ChromaDB · MiniLM embeddings.<br>'
        'Chunks outside your clearance are removed before the model sees anything.</div>',
        unsafe_allow_html=True,
    )


# ─── MAIN ─────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="vq-topbar">
  <div class="vq-topbar-title"><span class="vq-dot"></span>Secure session</div>
  <div style="display:flex;gap:8px;flex-wrap:wrap">
    <span class="vq-chip"><b>{esc(current_user['name'])}</b> · {esc(role.replace('_', ' '))}</span>
    <span class="vq-chip">{esc(model_name)}</span>
  </div>
</div>""", unsafe_allow_html=True)

typed = st.chat_input("Ask about finance, HR, security, operations or compliance…")
new_q = typed or st.session_state.pop("queued_prompt", None)

if not st.session_state.messages and not new_q:
    first = esc(current_user["name"].split()[0])
    st.markdown(f"""
    <div class="vq-hero">
      <h1>Ask across everything you're cleared to see.</h1>
      <p>Welcome, {first}. Answers come only from sources your role can open, and every claim
      points back to the document, table or log it came from.</p>
    </div>
    <div class="vq-h">Try one of these for the {esc(role.replace('_', ' '))} role</div>
    """, unsafe_allow_html=True)

    suggestions = ROLE_QUERIES.get(role, ROLE_QUERIES["employee"])
    cols = st.columns(2)
    for i, s in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(s, key=f"sug_{i}", use_container_width=True):
                st.session_state.queued_prompt = s
                st.rerun()

    st.markdown("""
    <div class="vq-h">What happens to your question</div>
    <div class="vq-flow">
      <div class="vq-step"><span class="vq-step-n">1</span><div class="vq-step-t">Check clearance</div>
        <div class="vq-step-d">Your identity and role are resolved from the access policy. Restricted topics stop here.</div></div>
      <div class="vq-step"><span class="vq-step-n">2</span><div class="vq-step-t">Route</div>
        <div class="vq-step-d">The question is matched to the most relevant kind of source: documents, tables or logs.</div></div>
      <div class="vq-step"><span class="vq-step-n">3</span><div class="vq-step-t">Retrieve</div>
        <div class="vq-step-d">Semantic search finds candidate passages. Anything you can't access is dropped.</div></div>
      <div class="vq-step"><span class="vq-step-n">4</span><div class="vq-step-t">Answer</div>
        <div class="vq-step-d">The model writes from the remaining passages only, with numbered citations.</div></div>
    </div>""", unsafe_allow_html=True)

# Existing conversation
for m in st.session_state.messages:
    if m["role"] == "user":
        render_user_msg(m)
    else:
        with st.chat_message("assistant", avatar="🔐"):
            render_assistant_msg(m, show_trace, show_chunks)

# New question
if new_q and new_q.strip():
    user_msg = {"role": "user", "content": new_q.strip(),
                "name": current_user["name"], "user_role": role.replace("_", " ")}
    st.session_state.messages.append(user_msg)
    render_user_msg(user_msg)

    with st.chat_message("assistant", avatar="🔐"):
        with st.spinner("Checking clearance, retrieving sources, drafting a cited answer…"):
            reply = run_query(pipeline, user_msg["content"], current_user, top_k)
        reply["user_role"] = role.replace("_", " ")
        st.session_state.messages.append(reply)
        render_assistant_msg(reply, show_trace, show_chunks)
"""Streamlit UI cho Research Agent.

Chạy:  streamlit run app.py
Tái dùng vòng lặp model -> tool trong chat.py, nên transcript có cùng định dạng
(transcripts/*.transcript.json) và có thể nộp như bằng chứng live chat.
"""
from __future__ import annotations

import html
import json
import time
from datetime import datetime

import streamlit as st

import chat
from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
TRANSCRIPTS_DIR = ROOT / "transcripts"
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4
APP_NAME = "Research Agent"

# (icon, title, subtitle, prompt)
EXAMPLES = [
    ("📰", "Tin tức hôm nay", "Tin nổi bật về AI trong ngày", "Tin tức AI hôm nay có gì nổi bật?"),
    ("🐦", "Bài đăng của một người", "Tweet mới nhất của một tài khoản", "Tweet mới nhất của Sam Altman là gì?"),
    ("✉️", "Gửi bản tin", "Luôn hỏi xác nhận trước khi gửi", "Đăng bản tin này lên Telegram giúp mình"),
]

st.set_page_config(page_title=APP_NAME, page_icon="✨", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&display=swap');

:root {
  --bg: #FAF9F6; --ink: #1B1A17; --muted: #6B6A66; --line: #E7E4DD;
  --accent: #6D5BD0; --accent-soft: #EFEBFB;
  --side: #1F1E1C; --side-2: #2B2A27; --side-ink: #ECEAE4; --side-muted: #8D8B85;
}
.stApp {background: var(--bg);}
#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}
.block-container {padding-top: 1rem; padding-bottom: 7rem; max-width: 860px;}

/* ---------- sidebar (dark) ---------- */
section[data-testid="stSidebar"] {background: var(--side); border-right: none;}
section[data-testid="stSidebar"] * {color: var(--side-ink);}
section[data-testid="stSidebar"] .stButton > button {
  background: var(--side-2); border: 1px solid #3B3A36; color: var(--side-ink);
  border-radius: 12px; padding: 0.7rem 1rem; font-weight: 600; text-align: left;
}
section[data-testid="stSidebar"] .stButton > button:hover {border-color: #55534D; background: #34332F;}
section[data-testid="stSidebar"] [data-testid="stExpander"] {
  border: 1px solid #3B3A36; border-radius: 12px; background: transparent;
}
.brand {display: flex; align-items: center; gap: 0.7rem; margin: 0.2rem 0 1.2rem;}
.brand .logo {width: 34px; height: 34px; border-radius: 10px; background: #DDEB63;
  display: flex; align-items: center; justify-content: center; color: #1F1E1C !important;
  font-size: 1.1rem; font-weight: 700;}
.brand .name {font-family: 'Playfair Display', 'Times New Roman', Georgia, serif; font-size: 1.35rem; color: #fff;}
.side-label {font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--side-muted) !important; margin: 1.4rem 0 0.4rem; display: flex; justify-content: space-between;}
.recent {display: flex; justify-content: space-between; gap: 0.6rem; padding: 0.45rem 0.2rem;
  font-size: 0.9rem; border-radius: 8px;}
.recent .t {overflow: hidden; text-overflow: ellipsis; white-space: nowrap;}
.recent .d {color: var(--side-muted) !important; font-size: 0.78rem; flex-shrink: 0;}
.empty {color: var(--side-muted) !important; font-size: 0.85rem; padding: 0.3rem 0.2rem;}

/* ---------- top bar ---------- */
.topbar {display: flex; align-items: center; gap: 0.55rem; padding: 0.4rem 0 0.9rem;
  border-bottom: 1px solid var(--line); margin-bottom: 1rem;}
.topbar .spark {color: var(--accent); font-size: 1.1rem;}
.topbar .title {font-family: 'Playfair Display', 'Times New Roman', Georgia, serif; font-size: 1.05rem; color: var(--ink);}
.topbar .beta {font-size: 0.62rem; font-weight: 700; letter-spacing: 0.06em; color: var(--accent);
  background: var(--accent-soft); padding: 0.12rem 0.4rem; border-radius: 5px;}

/* ---------- hero ---------- */
.hero {text-align: center; padding: 2.2rem 0 1.4rem;}
.hero h1 {font-family: 'Playfair Display', 'Times New Roman', Georgia, serif; font-weight: 700; color: var(--ink);
  font-size: 3.3rem; line-height: 1.06; letter-spacing: -0.01em; margin: 0 auto; max-width: 640px;}
.hero p {color: var(--muted); font-size: 1.05rem; line-height: 1.55; margin: 1.1rem auto 0; max-width: 520px;}

/* ---------- ask card (form) ---------- */
div[data-testid="stForm"] {background: #fff; border: 1px solid var(--line); border-radius: 18px;
  padding: 0.6rem 0.8rem 0.5rem; box-shadow: 0 6px 24px rgba(31,30,28,0.05);}
div[data-testid="stForm"] textarea {border: none !important; box-shadow: none !important;
  background: transparent !important; font-size: 1rem; color: var(--ink);}
div[data-testid="stForm"] [data-baseweb="textarea"], div[data-testid="stForm"] [data-baseweb="base-input"] {
  background: transparent !important; border: none !important;}
.chip {display: inline-flex; align-items: center; gap: 0.4rem; color: var(--muted); font-size: 0.86rem; padding-top: 0.55rem;}
div[data-testid="stForm"] .stFormSubmitButton > button {
  background: #C9C7C1; color: #fff; border: none; border-radius: 10px; width: 44px; height: 40px; float: right;}
div[data-testid="stForm"] .stFormSubmitButton > button:hover {background: var(--accent); color: #fff;}

/* ---------- suggestion cards ---------- */
.main div.stButton > button {
  background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 0.9rem 1rem;
  text-align: left; height: auto; white-space: normal; color: var(--ink); transition: all .15s ease;}
.main div.stButton > button:hover {border-color: var(--accent); background: #FBFAFF; color: var(--ink);
  transform: translateY(-1px);}
.main div.stButton > button p {margin: 0; line-height: 1.35;}
.section-label {color: var(--muted); font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em;
  text-transform: uppercase; margin: 1.6rem 0 0.5rem;}

/* ---------- conversation ---------- */
[data-testid="stChatMessage"] {background: transparent; border-radius: 16px; padding: 0.7rem 0.2rem;}
[data-testid="stChatInput"] {border-radius: 16px; background: #fff;}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_provider(name: str):
    return make_provider(name)


def new_transcript(provider_name: str, model: str | None, version: str) -> dict:
    artifact_version = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    tid = "_".join([safe_slug(version), safe_slug(provider_name), ts])
    return {
        "transcript_id": tid,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model,
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": HISTORY_WINDOW,
        "max_tool_rounds": MAX_TOOL_ROUNDS,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "source": "streamlit_ui",
        "turns": [],
    }


def is_network_error(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    return any(word in name for word in ("connection", "timeout", "connecterror"))


def run_with_retry(*, attempts: int = 3, **kwargs):
    """Retry on flaky-network errors only; any other error is raised immediately."""
    for attempt in range(1, attempts + 1):
        try:
            return chat.run_model_tool_loop(max_tool_rounds=MAX_TOOL_ROUNDS, **kwargs)
        except Exception as exc:
            if not is_network_error(exc) or attempt == attempts:
                raise
            time.sleep(1.5 * attempt)


def render_events(events: list[dict]) -> None:
    for ev in events:
        with st.expander(f"🔧 {ev['tool']}({json.dumps(ev['args'], ensure_ascii=False)})"):
            st.json(ev["result"], expanded=False)


def reset_conversation() -> None:
    for key in ("messages", "history", "transcript", "transcript_path"):
        st.session_state.pop(key, None)


# ---------------- State ----------------
st.session_state.setdefault("messages", [])  # for display
st.session_state.setdefault("history", [])  # for the model

# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown(
        f'<div class="brand"><div class="logo">✦</div><div class="name">{APP_NAME}</div></div>',
        unsafe_allow_html=True,
    )
    if st.button("＋  Nghiên cứu mới", use_container_width=True, key="new_chat"):
        reset_conversation()
        st.rerun()

    st.markdown('<div class="side-label"><span>Gần đây</span></div>', unsafe_allow_html=True)
    recent = [m["content"] for m in st.session_state["messages"] if m["role"] == "user"][-5:][::-1]
    if recent:
        for text in recent:
            label = html.escape(text if len(text) <= 34 else text[:33] + "…")
            st.markdown(
                f'<div class="recent"><span class="t">{label}</span><span class="d">Hôm nay</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<div class="empty">Chưa có câu hỏi nào.</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-label"><span>Cài đặt</span></div>', unsafe_allow_html=True)
    show_tools = st.toggle(
        "Hiện chi tiết tool",
        value=False,
        help="Hiển thị tool nào đã được gọi (và kết quả) dưới mỗi câu trả lời.",
    )
    with st.expander("⚙️ Nâng cao"):
        provider_name = st.selectbox(
            "Provider", ["openai", "openrouter", "anthropic", "gemini", "ollama"], index=0
        )
        model = st.text_input("Model (để trống = mặc định)", value="") or None
        version = st.text_input("Version label", value="v9")
        st.caption("Version chỉ là nhãn ghi vào transcript; prompt/tools lấy từ artifacts/ hiện tại.")

# ---------------- Top bar ----------------
st.markdown(
    f'<div class="topbar"><span class="spark">✦</span><span class="title">{APP_NAME}</span>'
    '<span class="beta">BETA</span></div>',
    unsafe_allow_html=True,
)

pending = st.session_state.pop("pending_input", None)

# ---------------- Welcome screen ----------------
if not st.session_state["messages"] and not pending:
    st.markdown(
        """
<div class="hero">
  <h1>Bạn muốn tìm hiểu điều gì hôm nay?</h1>
  <p>Tìm tin, đọc bài và tổng hợp thành bản tin ngắn gọn, có nguồn rõ ràng.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.form("ask_form", clear_on_submit=True, border=False):
        question = st.text_area(
            "Câu hỏi",
            placeholder="Nhập chủ đề hoặc câu hỏi nghiên cứu của bạn...",
            height=96,
            label_visibility="collapsed",
        )
        left, right = st.columns([5, 1])
        left.markdown('<div class="chip">🌐 Web · X/Twitter · arXiv</div>', unsafe_allow_html=True)
        with right:
            submitted = st.form_submit_button("➜", key="send")
    if submitted and question.strip():
        st.session_state["pending_input"] = question.strip()
        st.rerun()

    st.markdown('<div class="section-label">Thử ngay</div>', unsafe_allow_html=True)
    cols = st.columns(len(EXAMPLES))
    for i, (col, (icon, title, subtitle, prompt)) in enumerate(zip(cols, EXAMPLES)):
        with col:
            if st.button(f"{icon}  **{title}**\n\n{subtitle}", key=f"ex{i}", use_container_width=True):
                st.session_state["pending_input"] = prompt
                st.rerun()

# ---------------- Conversation ----------------
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"], avatar="🙂" if msg["role"] == "user" else "✨"):
        st.markdown(msg["content"])
        if show_tools and msg.get("events"):
            render_events(msg["events"])

typed = st.chat_input("Hỏi về tin tức, tài khoản X, hoặc dán một đường link...")
user_text = typed or pending

if user_text:
    st.session_state["messages"].append({"role": "user", "content": user_text})
    with st.chat_message("user", avatar="🙂"):
        st.markdown(user_text)

    if "transcript" not in st.session_state:
        st.session_state["transcript"] = new_transcript(provider_name, model, version)
        st.session_state["transcript_path"] = (
            TRANSCRIPTS_DIR / f"{st.session_state['transcript']['transcript_id']}.transcript.json"
        )
    transcript = st.session_state["transcript"]

    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    openai_tools = to_openai_tools(load_tool_declarations(TOOLS_PATH))
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state["history"], HISTORY_WINDOW),
        {"role": "user", "content": user_text},
    ]

    turn = {
        "turn_index": len(transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.chat_message("assistant", avatar="✨"):
        events: list[dict] = []
        try:
            with st.spinner("Đang tìm kiếm..."):
                result = run_with_retry(
                    provider=get_provider(provider_name),
                    messages=messages,
                    tools=openai_tools,
                    model=model,
                )
            turn.update(result)
            events = result["tool_events"]
            answer = result["assistant_text"] or "(không có nội dung)"
            st.session_state["history"] += [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": answer},
            ]
        except Exception as exc:  # hiển thị lỗi thay vì làm sập UI
            if is_network_error(exc):
                answer = (
                    "⚠️ Mất kết nối tới máy chủ AI (mạng chập chờn). "
                    "Bạn thử gửi lại câu hỏi sau vài giây nhé."
                )
            else:
                answer = f"⚠️ Lỗi: {type(exc).__name__}: {exc}"
            turn.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
        st.markdown(answer)
        if show_tools:
            render_events(events)

    turn["ended_at"] = now_iso()
    transcript["turns"].append(turn)
    write_transcript(st.session_state["transcript_path"], transcript)
    st.session_state["messages"].append({"role": "assistant", "content": answer, "events": events})

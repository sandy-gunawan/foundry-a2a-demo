r"""Streamlit chat playground for the Foundry Router Logic App.

Run:
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    # set the trigger URL (contains a secret sig=...), e.g. in a local .env:
    #   LOGIC_APP_URL=https://prod-XX.<region>.logic.azure.com:443/workflows/.../invoke?...&sig=...
    streamlit run playground.py

The Logic App URL is configured from the app's own Settings sidebar (stored on the
server so everyone using the page shares it). It also falls back to a LOGIC_APP_URL
env var / local .env if you prefer.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = Path(os.environ.get("CONFIG_PATH", "/tmp/playground_config.json"))
REQUEST_TIMEOUT_SECONDS = 120


def load_saved_url() -> str:
    """Read the shared URL from the config file, falling back to an env var."""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text()).get("logic_app_url", "")
        except (json.JSONDecodeError, OSError):
            pass
    return os.environ.get("LOGIC_APP_URL", "")


def save_url(url: str) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps({"logic_app_url": url}))
    except OSError as error:
        st.sidebar.error(f"Could not save config: {error}")


st.set_page_config(page_title="Foundry Router Playground", page_icon="🛎️")

if "logic_app_url" not in st.session_state:
    st.session_state.logic_app_url = load_saved_url()

with st.sidebar:
    st.header("⚙️ Settings")
    st.caption("Paste your Logic App trigger URL, then Save. It is stored on the server and shared by everyone using this page.")
    url_input = st.text_input("Logic App URL", value=st.session_state.logic_app_url, type="password")
    if st.button("Save URL", use_container_width=True):
        st.session_state.logic_app_url = url_input.strip()
        save_url(st.session_state.logic_app_url)
        st.success("Saved. Everyone using this page now uses this URL.")
    st.caption("✅ URL is configured." if st.session_state.logic_app_url else "⚠️ No URL set yet.")

st.title("🛎️ Foundry Router Playground")
st.caption("Type a message; it is classified and routed to the matching Foundry agent.")

logic_app_url = st.session_state.logic_app_url
if not logic_app_url or not logic_app_url.startswith("http"):
    st.info("Set your Logic App URL in the ⚙️ Settings sidebar (top-left ›) to start chatting.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

AGENT_LABELS = {
    "agt-billing": "🧾 Billing",
    "agt-techsupport": "🛠️ Tech Support",
}
INTENT_LABELS = {
    "billing": "🧾 Billing",
    "techsupport": "🛠️ Tech Support",
    "other": "🤖 Fallback",
}


def agent_label(agent: str, intent: str) -> str:
    """Friendly label for the agent that handled the message."""
    return AGENT_LABELS.get(agent) or INTENT_LABELS.get(intent) or "🤖 Router"


def parse_response(text: str) -> dict:
    """Accept plain text (answer only) OR structured JSON from the workflow."""
    try:
        data = json.loads(text)
        if isinstance(data, dict) and ("answer" in data or "intent" in data):
            return {
                "answer": data.get("answer") or "(no answer)",
                "intent": data.get("intent", ""),
                "agent": data.get("agent", ""),
                "model": data.get("model", ""),
                "usage": data.get("usage") or {},
            }
    except (json.JSONDecodeError, TypeError):
        pass
    return {"answer": text, "intent": "", "agent": "", "model": "", "usage": {}}


def render_trace(meta: dict) -> None:
    """One-line summary + an expandable detail table under a reply."""
    usage = meta.get("usage") or {}
    total_tokens = usage.get("total_tokens")
    summary = [
        f"**{agent_label(meta.get('agent', ''), meta.get('intent', ''))}**",
        f"⏱️ {meta.get('elapsed', 0.0):.1f}s",
    ]
    if total_tokens:
        summary.append(f"🔢 {total_tokens} tokens")
    if meta.get("status") and meta["status"] != 200:
        summary.append(f"⚠️ HTTP {meta['status']}")
    st.caption("  ·  ".join(summary))

    with st.expander("🔎 Trace details"):
        rows = {
            "Routed to (agent)": meta.get("agent") or "—",
            "Detected intent": meta.get("intent") or "—",
            "Model": meta.get("model") or "—",
            "HTTP status": meta.get("status") or "—",
            "Response time": f"{meta.get('elapsed', 0.0):.2f} s",
            "Handled at": meta.get("ts", "—"),
        }
        if usage:
            rows["Input tokens"] = usage.get("input_tokens", "—")
            rows["Output tokens"] = usage.get("output_tokens", "—")
            rows["Total tokens"] = usage.get("total_tokens", "—")
        st.table({"Field": list(rows.keys()), "Value": [str(v) for v in rows.values()]})


# Replay the conversation (each reply keeps its trace).
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["text"])
        if message["role"] == "assistant" and message.get("meta"):
            render_trace(message["meta"])

prompt = st.chat_input("Ask billing or tech support…")
if prompt:
    st.session_state.messages.append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Routing to the right agent…"):
            start = time.perf_counter()
            try:
                response = requests.post(
                    logic_app_url,
                    json={"message": prompt},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                raw, status = response.text or "", response.status_code
            except requests.RequestException as error:
                raw, status = f"Error calling the Logic App: {error}", 0
            elapsed = time.perf_counter() - start

        parsed = parse_response(raw)
        meta = {
            "agent": parsed["agent"],
            "intent": parsed["intent"],
            "model": parsed["model"],
            "usage": parsed["usage"],
            "elapsed": elapsed,
            "status": status,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        st.write(parsed["answer"])
        render_trace(meta)

    st.session_state.messages.append(
        {"role": "assistant", "text": parsed["answer"], "meta": meta}
    )
    st.rerun()

# --- Session stats panel (sidebar) ---
with st.sidebar:
    st.divider()
    st.header("📊 Session stats")
    handled = [
        m for m in st.session_state.messages
        if m["role"] == "assistant" and m.get("meta")
    ]
    st.metric("Messages handled", len(handled))
    if handled:
        by_agent: dict[str, int] = {}
        latencies: list[float] = []
        total_tokens = 0
        for m in handled:
            meta = m["meta"]
            key = agent_label(meta.get("agent", ""), meta.get("intent", ""))
            by_agent[key] = by_agent.get(key, 0) + 1
            latencies.append(meta.get("elapsed", 0.0))
            total_tokens += (meta.get("usage") or {}).get("total_tokens", 0) or 0
        st.caption("Calls by agent")
        for key, count in by_agent.items():
            st.write(f"- {key}: **{count}**")
        st.metric("Avg response time", f"{sum(latencies) / len(latencies):.1f} s")
        if total_tokens:
            st.metric("Total tokens", total_tokens)
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

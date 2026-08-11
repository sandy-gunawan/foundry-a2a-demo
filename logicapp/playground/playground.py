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

for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["text"])

prompt = st.chat_input("Ask billing or tech support…")
if prompt:
    st.session_state.messages.append({"role": "user", "text": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Routing to the right agent…"):
            try:
                response = requests.post(
                    logic_app_url,
                    json={"message": prompt},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                answer = response.text or "(empty response)"
            except requests.RequestException as error:
                answer = f"Error calling the Logic App: {error}"
        st.write(answer)

    st.session_state.messages.append({"role": "assistant", "text": answer})

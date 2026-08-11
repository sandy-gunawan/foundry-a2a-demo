"""Streamlit chat playground for the Foundry Router Logic App.

Run:
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    # set the trigger URL (contains a secret sig=...), e.g. in a local .env:
    #   LOGIC_APP_URL=https://prod-XX.<region>.logic.azure.com:443/workflows/.../invoke?...&sig=...
    streamlit run playground.py

The URL is read from the LOGIC_APP_URL environment variable (or a local .env),
so the secret never lives in the page or the repo.
"""
import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

LOGIC_APP_URL = os.environ.get("LOGIC_APP_URL", "")
REQUEST_TIMEOUT_SECONDS = 120

st.set_page_config(page_title="Foundry Router Playground", page_icon="🛎️")
st.title("🛎️ Foundry Router Playground")
st.caption("Type a message; it is classified and routed to the matching Foundry agent.")

if not LOGIC_APP_URL or not LOGIC_APP_URL.startswith("http"):
    st.error(
        "LOGIC_APP_URL is not configured yet. Set it in the Container App "
        "(Settings -> Secrets -> 'logic-app-url'), or in a local .env file."
    )
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
                    LOGIC_APP_URL,
                    json={"message": prompt},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                answer = response.text or "(empty response)"
            except requests.RequestException as error:
                answer = f"Error calling the Logic App: {error}"
        st.write(answer)

    st.session_state.messages.append({"role": "assistant", "text": answer})

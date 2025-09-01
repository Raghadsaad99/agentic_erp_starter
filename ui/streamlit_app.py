# ui/streamlit_app.py
import os
import json
import ast
import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="Agent-driven ERP System",
    page_icon="🤖",
    layout="wide"
)

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = "user_001"

# --- Sidebar settings ---
with st.sidebar:
    st.title("ERP System Settings")
    st.session_state.user_id = st.text_input(
        "User ID", value=st.session_state.user_id
    )
    default_api = os.getenv("API_URL", "http://127.0.0.1:8000/api/chat")
    api_url = st.text_input("API URL", value=default_api)

st.title("🤖 Agent-driven ERP System")
st.caption("Chat with your ERP system using natural language")


def render_content(content):
    """
    Renders:
      1) Raw HTML tables/styles
      2) Dicts with a 'type' key (error/text/table)
      3) JSON or Python‐repr strings
      4) List-of-lists/tuples
      5) Fallback to markdown
    """

    # 1) Raw HTML
    if isinstance(content, str) and content.lstrip().startswith(("<style", "<table")):
        st.markdown(content, unsafe_allow_html=True)
        return

    # 2) Structured dict
    if isinstance(content, dict) and content.get("type"):
        t = content["type"]

        if t == "error":
            st.error(content.get("message", "An error occurred."))
            return

        if t == "text":
            st.markdown(content.get("content", ""))
            return

        if t == "table":
            rows    = content.get("rows", [])
            headers = content.get("headers", [])

            valid_rows = (
                isinstance(rows, list)
                and all(isinstance(r, (list, tuple)) for r in rows)
            )
            valid_headers = (
                isinstance(headers, list)
                and all(isinstance(h, str) for h in headers)
            )

            if valid_rows and valid_headers:
                try:
                    df = pd.DataFrame(rows, columns=headers)
                    st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error("Error rendering table: data shape mismatch.")
                    st.exception(e)
                    st.json(content)
            else:
                st.error("Table payload malformed; showing raw JSON.")
                st.json(content)
            return

        # Unknown dict type
        st.json(content)
        return

    # 3) Try parsing strings as JSON or Python literal
    if isinstance(content, str):
        parsed = None
        s = content.strip()
        try:
            parsed = json.loads(s)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(s)
            except Exception:
                parsed = None

        if isinstance(parsed, dict) and parsed.get("type"):
            render_content(parsed)
            return

        if isinstance(parsed, list) and all(isinstance(r, (list, tuple)) for r in parsed):
            try:
                df = pd.DataFrame(parsed)
                st.dataframe(df, use_container_width=True)
            except Exception:
                st.write(parsed)
            return

    # 4) Raw list-of-lists
    if isinstance(content, list) and all(isinstance(r, (list, tuple)) for r in content):
        try:
            df = pd.DataFrame(content)
            st.dataframe(df, use_container_width=True)
        except Exception:
            st.write(content)
        return

    # 5) Fallback
    st.markdown(str(content))


# --- Render history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        render_content(msg["content"])


# --- Input & API call ---
if prompt := st.chat_input("What would you like to do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        render_content(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    api_url,
                    json={"user_id": st.session_state.user_id, "message": prompt},
                    timeout=30
                )
                resp.raise_for_status()
                ai_response = resp.json()
            except Exception as e:
                ai_response = {"type": "error", "message": str(e)}

            st.session_state.messages.append(
                {"role": "assistant", "content": ai_response}
            )
            render_content(ai_response)
"""AI Chat App: a simple chat website built with Streamlit and the Gemini API."""

import os

import streamlit as st
from google import genai

from chat_logic import (
    DEFAULT_INSTRUCTION,
    DEFAULT_MODEL,
    MAX_HISTORY_MESSAGES,
    ChatError,
    generate_reply,
)

st.set_page_config(page_title="AI Chat App", page_icon="💬")
st.title("💬 AI Chat App")
st.caption("Built with Python, Streamlit and the Gemini API")


def get_api_key():
    """Read the key from Streamlit secrets, or from an environment variable. Never from the code."""
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if key:
            return key
    except Exception:  # no secrets file or no such secret
        pass
    return os.environ.get("GEMINI_API_KEY", "")


api_key = get_api_key()
if not api_key:
    st.error(
        "API key not found. Add a secret named GEMINI_API_KEY "
        "(on Streamlit Cloud: App settings, then Secrets)."
    )
    st.stop()


@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)


client = get_client(api_key)

# ---- Session state (the chat history lives here) ----
if "messages" not in st.session_state:
    st.session_state.messages = []
if "usage" not in st.session_state:
    st.session_state.usage = {"input": 0, "output": 0, "total": 0, "calls": 0}

# ---- Sidebar: custom instructions, settings, token counter ----
with st.sidebar:
    st.header("Settings")
    instruction = st.text_area("Custom instructions", value=DEFAULT_INSTRUCTION, height=130)
    model = st.text_input("Model", value=DEFAULT_MODEL)
    temperature = st.slider("Creativity (temperature)", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.slider("Max reply length (tokens)", 100, 2000, 500, 100)
    history_limit = st.slider("Messages remembered", 2, 20, MAX_HISTORY_MESSAGES, 2)

    if st.button("New chat"):
        st.session_state.messages = []
        st.session_state.usage = {"input": 0, "output": 0, "total": 0, "calls": 0}
        st.rerun()

    st.divider()
    st.subheader("Token usage (this chat)")
    usage = st.session_state.usage
    st.metric("Total tokens", usage["total"])
    st.caption(
        f"Input: {usage['input']} | Output: {usage['output']} | Replies: {usage['calls']}"
    )
    st.caption(
        "Tokens are the small pieces of text the model reads and writes. "
        "Longer chats use more tokens, so only the last messages are sent."
    )

# ---- Show the chat so far ----
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("tokens"):
            st.caption(f"{message['tokens']} tokens")

# ---- New message ----
user_text = st.chat_input("Type your message...")
if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                result = generate_reply(
                    client,
                    st.session_state.messages,
                    model=model.strip() or DEFAULT_MODEL,
                    system_instruction=instruction,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    history_limit=history_limit,
                )
            st.markdown(result["text"])
            st.caption(f"{result['total_tokens']} tokens")
            st.session_state.messages.append(
                {"role": "assistant", "content": result["text"], "tokens": result["total_tokens"]}
            )
            st.session_state.usage["input"] += result["input_tokens"]
            st.session_state.usage["output"] += result["output_tokens"]
            st.session_state.usage["total"] += result["total_tokens"]
            st.session_state.usage["calls"] += 1
            st.rerun()
        except ChatError as error:
            st.error(f"{error} Your last message was not sent, so please send it again.")
            # take back the unanswered user message so the chat history stays clean
            st.session_state.messages.pop()

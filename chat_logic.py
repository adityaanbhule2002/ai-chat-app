"""Chat logic for the AI Chat App.

There is no Streamlit code in this file, so it is easy to test.
It handles: chat history, roles, settings, token usage and friendly errors.
"""

import time

from google.genai import types

DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_INSTRUCTION = "You are a friendly AI assistant. Answer clearly, in simple words."
MAX_HISTORY_MESSAGES = 10  # only the last messages are sent, to save tokens (cost control)


class ChatError(Exception):
    """An error with a message that is safe and clear to show to the user."""


def trim_history(messages, limit=MAX_HISTORY_MESSAGES):
    """Keep only the last `limit` messages. The history must start with a user message."""
    trimmed = list(messages[-limit:])
    while trimmed and trimmed[0]["role"] != "user":
        trimmed.pop(0)
    return trimmed


def to_contents(messages):
    """Turn app messages (roles: user / assistant) into Gemini contents (roles: user / model)."""
    contents = []
    for message in messages:
        role = "user" if message["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=message["content"])]))
    return contents


def friendly_error(error):
    """Turn an API error into a short, clear message for the user."""
    code = getattr(error, "code", None)
    text = str(error)
    if code == 429 or "RESOURCE_EXHAUSTED" in text:
        return "Too many requests right now (rate limit). Please wait a minute and try again."
    if code == 404 or "NOT_FOUND" in text:
        return "This model name was not found for your key. Change the model name in the sidebar."
    if code in (401, 403) or "API key" in text or "PERMISSION_DENIED" in text:
        return "Your API key was rejected. Check the GEMINI_API_KEY secret."
    if code == 400 or "INVALID_ARGUMENT" in text:
        return "The request was not accepted. Try a shorter message or different settings."
    if code in (500, 503, 504) or "UNAVAILABLE" in text:
        return "Google's server is busy. Please try again in a moment."
    return "Something went wrong while contacting the AI. Please try again."


def _is_retryable(error):
    code = getattr(error, "code", None)
    return code in (429, 503) or "RESOURCE_EXHAUSTED" in str(error) or "UNAVAILABLE" in str(error)


def generate_reply(
    client,
    messages,
    model=DEFAULT_MODEL,
    system_instruction=DEFAULT_INSTRUCTION,
    temperature=0.7,
    max_output_tokens=500,
    history_limit=MAX_HISTORY_MESSAGES,
    retries=1,
    wait_seconds=3,
):
    """Send the chat to Gemini and return {"text", "input_tokens", "output_tokens", "total_tokens"}.

    Raises ChatError with a friendly message if something goes wrong.
    """
    contents = to_contents(trim_history(messages, history_limit))
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    attempt = 0
    while True:
        try:
            response = client.models.generate_content(model=model, contents=contents, config=config)
            break
        except Exception as error:  # noqa: BLE001 - we turn every API error into a clear message
            if attempt < retries and _is_retryable(error):
                attempt += 1
                time.sleep(wait_seconds * attempt)
                continue
            raise ChatError(friendly_error(error)) from error

    text = getattr(response, "text", None)
    if not text:
        text = (
            "(No text came back. The reply may have been blocked, or the max reply length "
            "was too small. Try raising it in the sidebar.)"
        )

    usage = getattr(response, "usage_metadata", None)
    input_tokens = (getattr(usage, "prompt_token_count", 0) or 0) if usage else 0
    output_tokens = (getattr(usage, "candidates_token_count", 0) or 0) if usage else 0
    total_tokens = (getattr(usage, "total_token_count", 0) or 0) if usage else 0
    if not total_tokens:
        total_tokens = input_tokens + output_tokens

    return {
        "text": text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }

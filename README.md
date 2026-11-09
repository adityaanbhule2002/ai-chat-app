# AI Chat App

**Module 03: LLM APIs & Application Development**
Codomax Digital Solutions Internship | Aditya Nitin Anbhule

A simple chat website built with **Python**, **Streamlit** and the **Gemini API**. You type a message, the AI replies, and the app remembers the conversation.

## Features

- **Chat with an AI** using a text box and a chat history
- **Custom instructions** (the "system" role): tell the AI how to behave, for example "Explain like I am a beginner"
- **Chat memory:** the app sends the earlier messages (user and assistant roles) with every new message
- **Settings:** creativity (temperature), maximum reply length, and how many messages to remember
- **Token counter:** shows the tokens used by each reply and by the whole chat
- **Cost control:** only the last messages are sent, and the reply length is limited
- **Clear error messages** for rate limits, wrong model names, rejected keys and busy servers (with one automatic retry for rate limits and busy servers)
- **New chat** button to start again

## How it works

```
You type  ->  app.py (screen)  ->  chat_logic.py (history, settings, errors)  ->  Gemini API
                  ^                                                                  |
                  +----------------------------- reply + token count <---------------+
```

| File | What it does |
|---|---|
| `app.py` | The screen: sidebar settings, chat history, text box |
| `chat_logic.py` | Builds the message list, calls the API, counts tokens, turns errors into clear messages |
| `requirements.txt` | The Python packages needed |
| `.gitignore` | Keeps secret files out of GitHub |

## API key (important)

The API key is **never written in the code**. The app reads a secret named `GEMINI_API_KEY`:

- **On Streamlit Community Cloud:** App settings, then Secrets, then add `GEMINI_API_KEY = "your-key"`
- **On your own computer:** set an environment variable named `GEMINI_API_KEY`, or create `.streamlit/secrets.toml` with the same line (this file is ignored by Git)

Get a free key at https://aistudio.google.com/apikey.

## Run it on your computer

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Which model, and why

The default model is `gemini-3.5-flash-lite`. In my own timing test with one short question:

| Model | Time |
|---|---|
| `gemini-3.8-flash` | 333 seconds |
| `gemini-3.5-flash-lite` | 0.8 seconds |

A chat that waits minutes for each reply is not usable, so I chose the faster model. The model name can be changed in the sidebar.

## Limits and notes

- The free tier has rate limits. If you send many messages quickly, the app shows a "too many requests" message.
- Free-tier content can be used by Google to improve its products, so **do not type private information** into the chat.
- The chat history is kept only while the page is open. Refreshing the page starts a new chat.
- Model names change over time. If a model is not found, change the name in the sidebar.

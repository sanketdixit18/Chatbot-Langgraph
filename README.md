# AI Chat Assistant — Streamlit UI for your LangGraph chatbot

A clean, modern chat interface wired directly to the LangGraph chatbot
from `chatbot.ipynb`. No responses are mocked — every message goes
through your real graph (`ChatGroq` + `InMemorySaver` + thread-based
state).

## Project structure

```text
chatbot-ui/
├── app.py              # Streamlit UI
├── chatbot.py           # Your chatbot logic, refactored from the notebook
├── requirements.txt
├── .env.example
└── README.md
```

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure your API key

Copy the example env file and add your Groq API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=your_actual_groq_api_key_here
```

Get a key at https://console.groq.com if you don't have one.

## 3. Run the app

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## How it works

### Thread ID / conversation memory

Your notebook's chatbot uses a LangGraph `InMemorySaver` checkpointer,
addressed by a `thread_id`:

```python
config = {"configurable": {"thread_id": thread_id}}
chatbot.invoke({"messages": [...]}, config=config)
```

The UI generates a fresh `thread_id` (a UUID) per conversation and
stores it in `st.session_state`. Every message you send in that
conversation is invoked with the same `thread_id`, so the graph's
checkpointer keeps the full message history and the model has
conversational memory — exactly as in your notebook's `while True`
loop.

Clicking **New chat** in the sidebar generates a new `thread_id`, so
the new conversation doesn't get mixed with previous ones, and starts
a fresh entry in the sidebar's conversation list.

Note: this app keeps the checkpointer in memory for the lifetime of
the running Streamlit process. Restarting the app clears all thread
history (same as re-running the notebook's kernel).

### Connecting UI to your chatbot

`app.py` never talks to the LLM directly. It only calls:

```python
from chatbot import get_ai_response
reply = get_ai_response(user_message, thread_id)
```

`get_ai_response()` in `chatbot.py` is a thin wrapper around your
original `chatbot.invoke(...)['messages'][-1].content` pattern.

## What came from your notebook vs. what was added

**From your notebook (`chatbot.ipynb`), unchanged:**
- The `ChatGroq(model="openai/gpt-oss-120b", temperature=0)` model
- The `ChatState` / `chatState` TypedDict with `Annotated[list[BaseMessage], add_messages]`
- The `chat_node` function and its logic
- The graph wiring: `START -> chat_node -> END`
- The `InMemorySaver` checkpointer
- The `thread_id`-based config pattern for `invoke()`
- Extracting the reply via `result["messages"][-1].content`

**Added for the UI (`app.py`, plus light wrapping in `chatbot.py`):**
- `build_chatbot()` / `get_ai_response()` — the notebook's cells wrapped
  in functions so they're importable, instead of top-level notebook code
- A `GROQ_API_KEY` presence check with a clear error message
- The entire Streamlit interface: chat bubbles, sidebar with new-chat and
  conversation switching, typing indicator, empty state, error handling,
  responsive/mobile CSS, and Enter-to-send (native to `st.chat_input`)
- `requirements.txt`, `.env.example`, this `README.md`

No model, prompt, state schema, or graph behavior was changed from your
original implementation.

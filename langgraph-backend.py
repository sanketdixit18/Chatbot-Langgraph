"""
Core chatbot logic — refactored (not rewritten) from chatbot.ipynb.

Original notebook implementation preserved as-is:
- Model: ChatGroq("openai/gpt-oss-120b", temperature=0)
- State: TypedDict with a single `messages` field using add_messages
- Graph: single `chat_node` wired START -> chat_node -> END
- Checkpointer: InMemorySaver, addressed via {"configurable": {"thread_id": ...}}

The only change made here is wrapping this logic in functions so a UI
(app.py) can import and call it. No model, prompt, or graph behavior
was altered.
"""
import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
import time

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise EnvironmentError(
        "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
    )

# --- from the notebook: model ---
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


# --- from the notebook: state definition ---
class ChatState(TypedDict):
    """Conversation state: a running list of messages, merged via add_messages."""

    messages: Annotated[list[BaseMessage], add_messages]


# --- from the notebook: the single graph node ---
def chat_node(state: ChatState) -> dict:
    """Send the current message history to the LLM and return its reply."""
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def build_chatbot():
    """Compile the LangGraph chatbot graph with an in-memory checkpointer.

    Same graph shape as the notebook: START -> chat_node -> END,
    compiled with an InMemorySaver checkpointer for per-thread memory.
    """
    checkpointer = InMemorySaver()
    graph = StateGraph(ChatState)

    graph.add_node("chat_node", chat_node)
    graph.add_edge(START, "chat_node")
    graph.add_edge("chat_node", END)

    return graph.compile(checkpointer=checkpointer)


# Singleton compiled graph, reused across requests so thread memory persists
# for the lifetime of the Streamlit process.
chatbot = build_chatbot()


# def get_ai_response(user_message: str, thread_id: str) -> str:
#     """
#     Send a user message to the chatbot for a given conversation thread
#     and return the AI's text response.

#     This mirrors the notebook's invoke pattern exactly:
#         chatbot.invoke({"messages": [HumanMessage(...)]}, config=config)
#     """
#     config = {"configurable": {"thread_id": thread_id}}
#     result = chatbot.invoke(
#         {"messages": [HumanMessage(content=user_message)]},
#         config=config,
#     )
#     return result["messages"][-1].content

# def stream_ai_response(user_message: str, thread_id: str):
#     """
#     Stream the AI response token-by-token for a given conversation thread.
#     """

#     config = {
#         "configurable": {
#             "thread_id": thread_id
#         }
#     }

#     for message, metadata in chatbot.stream(
#         {
#             "messages": [
#                 HumanMessage(content=user_message)
#             ]
#         },
#         config=config,
#         stream_mode="messages"
#     ):
#         # Only stream AI-generated content
#         if message.content:
#             yield message.content


def stream_ai_response(user_message: str, thread_id: str):
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    buffer = ""
    last_flush = time.time()

    for message, metadata in chatbot.stream(
        {
            "messages": [
                HumanMessage(content=user_message)
            ]
        },
        config=config,
        stream_mode="messages",
    ):
        if not message.content:
            continue

        buffer += message.content

        # Send chunks smoothly every ~30ms
        if time.time() - last_flush >= 0.03:
            yield buffer
            buffer = ""
            last_flush = time.time()

    # Send anything remaining
    if buffer:
        yield buffer


def get_thread_messages(thread_id: str):
    """
    Get the saved messages for a specific LangGraph thread.
    """
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    state = chatbot.get_state(config)

    if not state or not state.values:
        return []

    messages = state.values.get("messages", [])

    return [
        {
            "role": "user" if message.type == "human" else "assistant",
            "content": message.content
        }
        for message in messages
        if message.type in ["human", "ai"]
    ]




config = {
    "configurable": {
        "thread_id": "thread-1"
    }
}


result = chatbot.invoke(
        {"messages": [HumanMessage(content="what is my name")]},
        config=config,
    )


print(result)
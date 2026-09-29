import uuid

import streamlit as st

from chatbot import (
    stream_ai_response,
    retrieve_all_threads,
    get_thread_messages,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Chat Assistant",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 6rem;
        max-width: 850px;
    }

    [data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.2);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_conversation(
    thread_id,
    messages=None
):
    """
    Create a conversation dictionary.
    """

    if messages is None:
        messages = []

    title = "New chat"

    # Generate title from first user message
    for message in messages:

        if message["role"] == "user":

            title = message["content"].strip()

            if len(title) > 30:
                title = title[:30] + "..."

            break

    return {
        "thread_id": thread_id,
        "title": title,
        "messages": messages,
    }


def get_active_conversation():
    """
    Return the currently active conversation.
    """

    active_thread_id = (
        st.session_state["active_thread_id"]
    )

    for conversation in st.session_state[
        "conversations"
    ]:

        if (
            conversation["thread_id"]
            == active_thread_id
        ):

            return conversation

    return None


# ============================================================
# LOAD CONVERSATIONS
# ============================================================

if "conversations" not in st.session_state:

    conversations = []

    # Get all thread IDs from SQLite
    thread_ids = retrieve_all_threads()

    # Load every saved conversation
    for thread_id in thread_ids:

        messages = get_thread_messages(
            thread_id
        )

        conversation = create_conversation(
            thread_id,
            messages
        )

        conversations.append(
            conversation
        )

    # Sort so conversations with messages
    # appear before empty conversations
    conversations.sort(
        key=lambda conversation: len(
            conversation["messages"]
        ),
        reverse=True,
    )

    # If database has no conversations,
    # create a new conversation
    if not conversations:

        first_thread_id = str(
            uuid.uuid4()
        )

        conversations.append(
            create_conversation(
                first_thread_id
            )
        )

    st.session_state[
        "conversations"
    ] = conversations

    st.session_state[
        "active_thread_id"
    ] = conversations[0]["thread_id"]


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "### 💬 Conversations"
    )

    # ========================================================
    # NEW CHAT
    # ========================================================

    if st.button(
        "➕ New chat",
        use_container_width=True,
    ):

        new_thread_id = str(
            uuid.uuid4()
        )

        new_conversation = create_conversation(
            new_thread_id
        )

        # Add to beginning
        st.session_state[
            "conversations"
        ].insert(
            0,
            new_conversation
        )

        # Make active
        st.session_state[
            "active_thread_id"
        ] = new_thread_id

        st.rerun()

    st.divider()

    # ========================================================
    # CONVERSATION LIST
    # ========================================================

    for conversation in st.session_state[
        "conversations"
    ]:

        thread_id = conversation[
            "thread_id"
        ]

        title = conversation[
            "title"
        ]

        is_active = (
            thread_id
            == st.session_state[
                "active_thread_id"
            ]
        )

        if is_active:

            button_label = (
                "🟢 " + title
            )

        else:

            button_label = (
                "⚪ " + title
            )

        if st.button(
            button_label,
            key=f"chat_{thread_id}",
            use_container_width=True,
        ):

            st.session_state[
                "active_thread_id"
            ] = thread_id

            st.rerun()

    st.divider()

    # ========================================================
    # THREAD INFORMATION
    # ========================================================

    st.caption(
        "Thread ID"
    )

    st.code(
        st.session_state[
            "active_thread_id"
        ][:12]
    )

    st.caption(
        "Powered by LangGraph + Groq"
    )


# ============================================================
# GET ACTIVE CONVERSATION
# ============================================================

active_conversation = (
    get_active_conversation()
)


if active_conversation is None:

    st.error(
        "Active conversation not found."
    )

    st.stop()


# ============================================================
# SYNC ACTIVE CONVERSATION WITH DATABASE
# ============================================================

thread_id = active_conversation[
    "thread_id"
]

database_messages = get_thread_messages(
    thread_id
)

if database_messages:

    active_conversation[
        "messages"
    ] = database_messages


# ============================================================
# HEADER
# ============================================================

st.markdown(
    "## 💬 AI Chat Assistant"
)

st.markdown(
    "Powered by LangGraph + Groq"
)


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

messages = active_conversation[
    "messages"
]


if not messages:

    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 5rem 1rem;
        ">

            <h2>👋 Start a conversation</h2>

            <p>
                Ask anything and start chatting
                with the AI.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )


else:

    for message in messages:

        if message["role"] == "user":

            avatar = "🧑"

        else:

            avatar = "🤖"

        with st.chat_message(
            message["role"],
            avatar=avatar,
        ):

            st.markdown(
                message["content"]
            )


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Type your message..."
)


# ============================================================
# PROCESS USER MESSAGE
# ============================================================

if user_input:

    thread_id = (
        active_conversation[
            "thread_id"
        ]
    )

    # ========================================================
    # UPDATE TITLE
    # ========================================================

    if (
        active_conversation["title"]
        == "New chat"
    ):

        title = user_input.strip()

        if len(title) > 30:

            title = title[:30] + "..."

        active_conversation[
            "title"
        ] = title

    # ========================================================
    # SAVE USER MESSAGE TO UI
    # ========================================================

    active_conversation[
        "messages"
    ].append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    # ========================================================
    # DISPLAY USER MESSAGE
    # ========================================================

    with st.chat_message(
        "user",
        avatar="🧑",
    ):

        st.markdown(
            user_input
        )

    # ========================================================
    # AI RESPONSE
    # ========================================================

    with st.chat_message(
        "assistant",
        avatar="🤖",
    ):

        try:

            reply = st.write_stream(
                stream_ai_response(
                    user_input,
                    thread_id,
                )
            )

            # ================================================
            # SAVE AI RESPONSE TO UI
            # ================================================

            active_conversation[
                "messages"
            ].append(
                {
                    "role": "assistant",
                    "content": reply,
                }
            )

        except Exception as exc:

            st.error(
                "Something went wrong "
                f"talking to the chatbot: {exc}"
            )
import streamlit as st

# ===============================
# Page Config
# ===============================
st.set_page_config(
    page_title="Praxa Theater Assistant",
    page_icon="🎭",
    layout="wide"
)

st.title("🎭 Praxa Theater Assistant")
st.caption("Ask me about the theater! 🎭")

# ===============================
# Cache RAG System
# ===============================
@st.cache_resource
def load_rag():
    import praxa_rag
    return praxa_rag

rag = load_rag()

# ===============================
# Chat History
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ===============================
# User Input
# ===============================
question = st.chat_input("Ask me about the theater!")

if question:

    # Show user message
    st.chat_message("user").markdown(question)

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    # ===============================
    # RAG CALL (SAFE)
    # ===============================
    try:
        response = rag.answer_and_sources(question)
        answer = response.get("answer", "")
        sources = response.get("sources", "")

    except Exception as e:
        answer = "⚠️ Sorry, I couldn't generate a response right now."
        sources = str(e)

    # ===============================
    # Assistant Response
    # ===============================
    with st.chat_message("assistant"):

        st.markdown(answer)

        if sources:
            st.markdown("### 📚 Sources")
            st.markdown(sources)

            # Advanced citation viewer
            with st.expander("🔍 Verified Sources", expanded=False):

                for i, src in enumerate(sources.split("\n"), start=1):
                    if src.strip():
                        st.markdown(f"{src}")

    # ===============================
    # Save History
    # ===============================
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"{answer}\n\n📚 Sources:\n{sources}"
    })
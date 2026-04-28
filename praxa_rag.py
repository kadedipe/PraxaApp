from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough, RunnableParallel
import sys
import os

# =========================
# IMPORT PROJECT MODULES
# =========================
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import context
import model
from praxa_model import get_model, SYSTEM_PROMPT


# =========================
# RETRIEVER
# =========================
retriever = context.get_vector_store().as_retriever()

question_and_docs = RunnableParallel({
    "question": RunnablePassthrough(),
    "context_docs": retriever
})


# =========================
# CONTEXT FORMATTER
# =========================
def make_context_string(inputs):
    return "\n\n".join(doc.page_content for doc in inputs["context_docs"])


context_chain = RunnablePassthrough.assign(
    context=make_context_string
)


# =========================
# MODEL
# =========================
llm, use_system_prompt = get_model()


# =========================
# PROMPT TEMPLATE
# =========================
if use_system_prompt:
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Question: {question}\n\nContext:\n{context}")
    ])
else:
    prompt_template = ChatPromptTemplate.from_messages([
        ("human",
         SYSTEM_PROMPT +
         "\n\nQuestion: {question}\n\nContext:\n{context}")
    ])


# =========================
# CHAIN
# =========================
answer_chain = context_chain | prompt_template | llm

chain_with_sources = question_and_docs.assign(answer=answer_chain)


# =========================
# MAIN FUNCTION
# =========================
def answer_and_sources(question: str) -> dict[str, str]:

    result = chain_with_sources.invoke(question)

    # Safe extraction of answer text
    response_text = getattr(result["answer"], "content", str(result["answer"]))

    # =========================
    # DEDUP SOURCES (FIXED)
    # =========================
    seen = set()
    unique_docs = []

    for doc in result["context_docs"]:
        key = (
            doc.metadata.get("source", "unknown"),
            doc.metadata.get("page", "unknown")
        )

        if key not in seen:
            seen.add(key)
            unique_docs.append(key)

    # =========================
    # FORMAT SOURCES
    # =========================
    sources_list = [
        f"[{i+1}] 📄 {src} — page {page}"
        for i, (src, page) in enumerate(unique_docs)
    ]

    sources = "\n".join(sources_list)

    return {
        "answer": response_text,
        "sources": sources
    }


# =========================
# TESTING
# =========================
if __name__ == "__main__":

    docs = retriever.invoke("What is Ryan Calais Cameron's most recent play?")
    print(f"Found {len(docs)} documents:\n")

    for doc in docs:
        print("-----")
        print(doc)

    print("\nFINAL ANSWER TEST:\n")

    result = answer_and_sources(
        "What is Ryan Calais Cameron's most recent play?"
    )

    print(result["answer"])
    print("\nSOURCES:\n")
    print(result["sources"])
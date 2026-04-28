import gdown
from pathlib import Path
from typing import Iterable, Optional

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# ==============================
# DOWNLOAD PDFs
# ==============================
def download_context_data(
    pdfs: Iterable[dict[str, str]],
    path: str = "./context_data"
) -> None:

    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)

    for pdf in pdfs:
        url = pdf["url"]
        filename = pdf["filename"]

        print(f"Downloading: {filename}")
        gdown.download(url, str(p / filename), quiet=False)


# ==============================
# LOAD DOCUMENTS
# ==============================
def load_context_data(path: str = "./context_data") -> list[Document]:
    loader = PyPDFDirectoryLoader(path)
    docs = loader.load()

    if not docs:
        raise ValueError("No documents found in context_data folder.")

    return docs


# ==============================
# CHUNK DOCUMENTS
# ==============================
def chunk_context_data(context_data: list[Document]) -> list[Document]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    return splitter.split_documents(context_data)


# ==============================
# EMBEDDINGS
# ==============================
def get_embedding_model(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> HuggingFaceEmbeddings:

    return HuggingFaceEmbeddings(model_name=model_name)


# ==============================
# VECTOR STORE (CREATE)
# ==============================
def create_vector_store(
    chunks: list[Document],
    embedding_model: Optional[Embeddings] = None,
    path: str = "./chromadb"
) -> Chroma:

    embedding_model = embedding_model or get_embedding_model()

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=path,
    )

    vector_store.persist()  # IMPORTANT FIX

    return vector_store


# ==============================
# VECTOR STORE (LOAD)
# ==============================
def get_vector_store(
    embedding_model: Optional[Embeddings] = None,
    path: str = "./chromadb"
) -> Chroma:

    embedding_model = embedding_model or get_embedding_model()

    return Chroma(
        persist_directory=path,
        embedding_function=embedding_model,
    )


# ==============================
# TEST PIPELINE
# ==============================
if __name__ == "__main__":

    pdfs = (
        {
            "url": "https://quanticedu.github.io/praxa/Longest Running Shows on Broadway 2025.pdf",
            "filename": "broadway.pdf",
        },
        {
            "url": "https://quanticedu.github.io/praxa/Every play and musical coming to the West End in 2025.pdf",
            "filename": "west_end.pdf",
        },
    )

    download_context_data(pdfs)

    docs = load_context_data()
    chunks = chunk_context_data(docs)

    embedding_model = get_embedding_model()

    vector_store = create_vector_store(chunks, embedding_model)

    print(f"Loaded pages: {len(docs)}")
    print(f"Chunks created: {len(chunks)}")

    results = vector_store.similarity_search(
        "A play written by Ryan Calais Cameron"
    )

    print("\nTop Retrieved Chunks:\n")

    for r in results:
        print(r.page_content[:300])
        print("-----")
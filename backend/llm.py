import os
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.docstore.document import Document
from dotenv import load_dotenv

load_dotenv()

# Example: gpt-4o-mini endpoint (adjust as needed)
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini") 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Directory with PDF lore documents
LORE_PDF_DIR = "./backend/lore_pdfs"

def load_and_index_pdfs(pdf_dir: str) -> FAISS:
    # In production, you'd do this indexing once and store the index.
    # For simplicity, we do it on startup. Consider caching or persisting.
    docs = []
    for file in os.listdir(pdf_dir):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(pdf_dir, file))
            pdf_docs = loader.load()
            docs.extend(pdf_docs)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    splitted_docs = text_splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vector_store = FAISS.from_documents(splitted_docs, embeddings)
    return vector_store

# Initialize vector store at startup
VECTOR_STORE = load_and_index_pdfs(LORE_PDF_DIR)

def get_llm():
    # Example: Using OpenAI with a custom model. Adjust as needed.
    # If "gpt-4o-mini" is a known openAI model variant, else set appropriate params.
    llm = OpenAI(
        openai_api_key=OPENAI_API_KEY,
        model_name=LLM_MODEL,
        temperature=0.7
    )
    return llm

def get_vectorstore():
    return VECTOR_STORE

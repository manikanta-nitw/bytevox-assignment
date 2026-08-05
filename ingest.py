import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

load_dotenv()

DATA_DIR = "./data"

def load_documents():
    print("Loading documents from data folder...")
    
    txt_loader = DirectoryLoader(
        DATA_DIR, 
        glob="**/*.txt", 
        loader_cls=TextLoader, 
        loader_kwargs={"encoding": "utf-8"}
    )
    txt_docs = txt_loader.load()
    
    pdf_loader = DirectoryLoader(
        DATA_DIR, 
        glob="**/*.pdf", 
        loader_cls=PyMuPDFLoader
    )
    pdf_docs = pdf_loader.load()
    
    md_loader = DirectoryLoader(
        DATA_DIR, 
        glob="**/*.md", 
        loader_cls=TextLoader, 
        loader_kwargs={"encoding": "utf-8"}
    )
    md_docs = md_loader.load()
    
    all_docs = txt_docs + pdf_docs + md_docs
    print(f"Loaded {len(all_docs)} documents.")
    return all_docs

def process_and_index():
    docs = load_documents()
    if not docs:
        print("No documents found in the ./data directory! Please check your data folder.")
        return

    # Chunking Strategy: 512 tokens with 50 overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    
    print("Splitting documents into chunks...")
    chunks = text_splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks.")
    
    # Free local embedding model running on CPU
    print("Downloading/Loading local HuggingFace embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print("Indexing chunks into Qdrant vector store...")
    QdrantVectorStore.from_documents(
        chunks,
        embeddings,
        path="./qdrant_data",
        collection_name="bytevox_docs",
    )
    
    print("Ingestion complete! Vector database is ready.")

if __name__ == "__main__":
    process_and_index()
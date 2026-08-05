from fastapi import FastAPI
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_qdrant import QdrantVectorStore
from transformers import pipeline

# Initialize FastAPI App
app = FastAPI(title="ByteVox RAG API")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("Loading Embedding Model and Vector Database...")
# 1. Load the exact same embedding model used for ingestion
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Connect to the existing Qdrant vector database we just built
vector_store = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    path="./qdrant_data",
    collection_name="bytevox_docs",
)
# Setup the retriever to fetch the top 3 most relevant chunks
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

print("Loading Local LLM (this may take a moment on the first run)...")
# 3. Setup a lightweight, free local LLM for generation
hf_pipeline = pipeline("text-generation", model="HuggingFaceTB/SmolLM-135M-Instruct", max_new_tokens=256)
llm = HuggingFacePipeline(pipeline=hf_pipeline)

# Define the expected JSON request format
class QueryRequest(BaseModel):
    question: str

@app.post("/query")
async def query_documents(request: QueryRequest):
    """
    Accepts a question, retrieves relevant document chunks, 
    and generates an answer grounded in the sources.
    """
    # Retrieve relevant chunks from Qdrant
    docs = retriever.invoke(request.question)
    
    # Extract the text and unique source filenames
    context = "\n\n".join([doc.page_content for doc in docs])
    sources = list(set([doc.metadata.get("source", "unknown").split("\\")[-1].split("/")[-1] for doc in docs]))
    
    # Construct the prompt to ground the LLM
    prompt = (
        f"Answer the question based strictly on the context provided below.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {request.question}\n\n"
        f"Answer:"
    )
    
    # Generate the answer
    answer = llm.invoke(prompt)
    
    # Return the exact JSON structure requested by ByteVox
    return {
        "answer": answer.strip(),
        "sources": sources
    }
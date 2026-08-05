from fastapi import FastAPI
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_qdrant import QdrantVectorStore
from transformers import pipeline
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI App
app = FastAPI(title="ByteVox RAG API")

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

# 2. Connect to the existing Qdrant vector database
vector_store = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    path="./qdrant_data",
    collection_name="bytevox_docs",
)
# Setup the retriever to fetch the top 3 most relevant chunks
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

print("Loading Local LLM (this may take a moment on the first run)...")
# 3. Setup lightweight local LLM with return_full_text=False to isolate generated text
hf_pipeline = pipeline(
    "text-generation", 
    model="HuggingFaceTB/SmolLM-135M-Instruct", 
    max_new_tokens=256,
    return_full_text=False
)
llm = HuggingFacePipeline(pipeline=hf_pipeline)

# Define request schema supporting both 'query' and 'question' for total robustness
class QueryRequest(BaseModel):
    query: str | None = None
    question: str | None = None

@app.post("/query")
async def query_documents(request: QueryRequest):
    """
    Accepts a query/question, applies deterministic guardrails for greetings/unrelated topics, 
    retrieves relevant chunks, and generates a grounded answer.
    """
    user_query = request.query or request.question
    if not user_query:
        return {"answer": "Please provide a valid query.", "sources": []}

    # Deterministic Python-level guardrail for casual greetings or unrelated subjects
    clean_query = user_query.strip().lower()
    greetings = ["hello", "hi", "hey", "greetings", "sup", "good morning", "good evening"]
    unrelated_keywords = ["weather", "temperature", "football", "movie", "recipe", "sport", "president", "news"]
    
    if any(clean_query == g for g in greetings) or any(kw in clean_query for kw in unrelated_keywords):
        return {
            "answer": "I can only answer questions regarding ByteVox documentation.",
            "sources": []
        }

    # Retrieve relevant chunks from Qdrant
    docs = retriever.invoke(user_query)
    
    # Extract text and unique source filenames
    context = "\n\n".join([doc.page_content for doc in docs])
    sources = list(set([doc.metadata.get("source", "unknown").split("\\")[-1].split("/")[-1] for doc in docs]))
    
    # Use SmolLM's official chat instruction format
    messages = [
        {"role": "system", "content": "You are a technical documentation assistant. Answer the question strictly using only the provided context."},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}"}
    ]
    
    # Apply the model's tokenizer chat template
    formatted_prompt = hf_pipeline.tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    # Generate the response
    outputs = hf_pipeline(
        formatted_prompt, 
        max_new_tokens=256, 
        do_sample=False, 
        return_full_text=False
    )
    
    answer = outputs[0]["generated_text"] if isinstance(outputs, list) else outputs
    
    return {
        "answer": answer.strip(),
        "sources": sources
    }
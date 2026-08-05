import requests
import time

# The endpoint of your local FastAPI server
API_URL = "http://127.0.0.1:8000/query"

# 5 Benchmark questions based on the Nexus documentation
TEST_QUESTIONS = [
    "What is the memory limit for the cpu-small compute profile?",
    "How do I initialize the Nexus client in Python?",
    "What are the encryption standards used by Nexus for data at rest?",
    "Can you explain what the Control Plane does in the Nexus architecture?",
    "What changes were made in version 1.2.0 regarding vector search?"
]

def run_evaluation():
    print(f"{'='*60}")
    print(" BYTEVOX RAG SYSTEM - AUTOMATED EVALUATION PIPELINE")
    print(f"{'='*60}\n")
    
    total_time = 0
    passed = 0

    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"Test {i}/5: {question}")
        
        start_time = time.time()
        
        try:
            # Send the POST request to your API
            response = requests.post(API_URL, json={"question": question})
            response.raise_for_status() 
            
            data = response.json()
            latency = time.time() - start_time
            total_time += latency
            
            answer = data.get("answer", "No answer generated.")
            sources = data.get("sources", [])
            
            print(f"⏱️  Latency: {latency:.2f}s")
            print(f"📄 Sources Retrieved: {', '.join(sources) if sources else 'None'}")
            print(f"🤖 Answer : {answer.strip()}\n")
            passed += 1
            
        except Exception as e:
            print(f"❌ Error occurred: {e}\n")

    print(f"{'='*60}")
    print(f" EVALUATION COMPLETE")
    print(f" Score: {passed}/5 Tests Successful")
    print(f" Average Latency: {(total_time/5):.2f}s per query")
    print(f"{'='*60}")

if __name__ == "__main__":
    run_evaluation()
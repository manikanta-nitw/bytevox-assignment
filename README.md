# ⚡ ByteVox Neural Core: RAG Evaluation System

A full-stack, entirely localized Retrieval-Augmented Generation (RAG) pipeline built to evaluate AI query accuracy against proprietary platform documentation. 

This project was engineered to balance robust backend vector retrieval with an ultra-premium, high-performance user interface.

## 🏗️ System Architecture

*   **Frontend Engine:** React, Vite, Tailwind CSS v3
*   **Backend API:** Python, FastAPI, Uvicorn
*   **Vector Database:** Qdrant (Local File-Based)
*   **AI Inference:** HuggingFace `SmolLM-135M` (Local CPU Execution)
*   **Embeddings:** `all-MiniLM-L6-v2` via SentenceTransformers

## ✨ UI / UX Design Philosophy

The frontend deviates from standard dashboard templates to deliver a "Neural Core" aesthetic:
*   **Deep Dark Mode & Glassmorphism:** Utilizes deep charcoal/black palettes accented with translucent, frosted-glass panels (`backdrop-blur-3xl`).
*   **Dynamic Data Reveal:** Engineered a strict CSS-grid "door-opening" animation to smoothly reveal source telemetry without cluttering the primary conversational interface.
*   **Luxury Accents:** Subdued deep reds and gold typography tracking simulate high-end proprietary engineering software.

## 🚀 Quick Start Guide

### 1. Initialize the Backend
Ensure you have Python 3.10+ installed. Navigate to the root directory:

```bash
# Create and activate the virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Install dependencies and populate the vector database
pip install -r requirements.txt
python ingest.py

# Launch the FastAPI Server
uvicorn api:app --reload any of this is cona=taining in this??
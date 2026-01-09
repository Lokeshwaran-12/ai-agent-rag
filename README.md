# AI Agent RAG System 🤖

Welcome to the AI Agent RAG System project! This is a smart AI assistant that can answer general questions and, more importantly, look up internal company documents to provide factual answers using Retrieval-Augmented Generation (RAG).

---

## 🏗️ Architecture Overview

The system is designed as an intelligent "Agent" that makes decisions on how to answer your questions.

**How it works (The Flow):**
1.  **You ask a question.**
2.  **The Agent thinks:** "Do I know this, or do I need to look it up?"
    *   *If it's general (e.g., "What is 2+2?"):* It answers directly.
    *   *If it's about the company (e.g., "Sick leave policy?"):* It uses the **Search Tool**.
3.  **The Search Tool (RAG):**
    *   Converts your question into numbers (Vectors).
    *   Finds the most relevant paragraph from the uploaded documents using **FAISS**.
    *   Sends that paragraph back to the Agent.
4.  **The Final Answer:**
    *   The Agent reads the paragraph and answers your question strictly based on facts.

---

## 💻 Tech Stack

We chose these technologies to make the system fast, reliable, and production-ready:

*   **Language:** Python 3.9+ (The standard for AI).
*   **Backend:** FastAPI (Modern, super fast web framework).
*   **AI Models:** Azure OpenAI
    *   *Reasoning:* `gpt-oss-120b` (Smart decision making).
    *   *Embeddings:* `text-embedding-3-small` (Converting text to vectors).
*   **Vector Database:** FAISS (Facebook AI Similarity Search) - extremely fast local search.
*   **Containerization:** Docker (Runs everywhere).

---

## 🛠️ Setup Instructions

### 1. Run Locally (The easy way)

**Prerequisites:** Python 3.9+ installed.

1.  **Setup the environment:**
    ```bash
    ./start.sh
    ```
    This script installs dependencies and starts the server.

2.  **Ingest Documents (Feed the brain):**
    Open a new terminal and run:
    ```bash
    curl -X POST "http://localhost:8000/ingest" \
      -H "Content-Type: application/json" \
      -d '{ "document_paths": ["data/documents/company_policy.txt", "data/documents/product_faq.txt"] }'
    ```

3.  **Ask Questions:**
    ```bash
    curl -X POST "http://localhost:8000/ask" \
      -H "Content-Type: application/json" \
      -d '{"query": "How many sick days do I get?"}'
    ```

### 2. Azure Deployment (Cloud)

1.  **Login to Azure:**
    ```bash
    az login
    ```
2.  **Run the deployment script:**
    ```bash
    ./deploy_azure.sh
    ```
    This will containerize the app and push it to an Azure App Service.

---

## 💡 Design Decisions

*   **Why FAISS instead of Pinecone/Chroma?**
    FAISS is lightweight and runs locally. It doesn't require an external API key or complex setup, making this project self-contained and easy to test.

*   **Why "Agentic" instead of simple RAG?**
    Simple RAG retrieves documents for *every* query, even "Hello". Our Agent is smarter—it only searches when necessary, saving costs and latency.

*   **Strict Factuality:**
    We deliberately engineered the system prompts to be strict (*"Do not assume"*). This is critical for business use cases like HR policies where "guessing" is dangerous.

---

## 🚧 Limitations & Future Improvements

**Current Limitations:**
*   **Memory:** The conversation history is stored in memory. If you restart the server, the bot forgets previous chats.
*   **File Support:** Currently optimized for Text (`.txt`) and specifically formatted `.pdf` files. Complex PDFs (with tables) might need better parsing.

**Future Improvements:**
*   **Add a Frontend:** Build a React/Next.js UI so users don't have to use `curl`.
*   **Persistent Database:** Use Redis or PostgreSQL to save chat history permanently.
*   **Advanced Parsing:** Integrate LlamaParse or Azure Document Intelligence for reading complex PDFs.

---

*Project created by [Your Name]*

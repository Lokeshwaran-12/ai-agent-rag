# 🚀 How to Run the AI Agent RAG System

This guide will help you set up and run the AI Agent RAG system on your local machine.

## ✅ Prerequisites

Ensure you have the following installed:
- **Python 3.9+**
- **Virtual Environment** (recommended)

---

## 🛠️ Step 1: Setup

1. **Clone/Open the project folder**:
   ```bash
   cd /path/to/project
   ```

2. **Run the Setup Script**:
   This script checks dependencies, sets up the virtual environment, and installs requirements.
   ```bash
   ./start.sh
   ```
   *If the server starts automatically, press `Ctrl+C` to stop it so we can ingest documents first.*

---

## 📥 Step 2: Ingest Documents

Before asking questions, we need to load the company documents into the AI's "brain" (Vector Database).

**Open a new terminal** and run:

```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "document_paths": [
      "data/documents/company_policy.txt",
      "data/documents/product_faq.txt",
      "data/documents/api_documentation.txt"
    ]
  }'
```
*Expected Output:* `{"status":"success", "total_chunks": 28, ...}`

---

## 🏃 Step 3: Run the Server

If it's not already running:

```bash
source venv/bin/activate
./start.sh
```
The server will run on `http://localhost:8000`.

---

## 🧪 Step 4: Sample Questions to Test

Run these commands in a separate terminal window to test the agent's capabilities.

### 1. Document Search (RAG)
*Asks about specific company info.*
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many sick leave days does an employee receive?"}'
```

### 2. General Knowledge (No Retrieval)
*The agent knows it doesn't need documents for this.*
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of France?"}'
```

### 3. Reasoning & Calculation
*The agent uses its Calculator tool.*
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "If I have 10 vacation days and take 3 days off, how many are left?"}'
```

---

## ⚠️ Troubleshooting

- **Error: "Address already in use"**
  Run this to kill the old process:
  ```bash
  pkill -f "uvicorn"
  ```
- **Error: "Model not found"**
  Check your `.env` file and ensure `AZURE_OPENAI_DEPLOYMENT_NAME` is correct.

---
**Enjoy your AI Agent!** 🤖

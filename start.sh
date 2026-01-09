#!/bin/bash

# Startup script for AI Agent RAG System

echo "🚀 Starting AI Agent RAG System..."
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Run: source venv/bin/activate"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Copy .env.example to .env and configure your API keys"
    echo "Run: cp .env.example .env"
    exit 1
fi

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if documents are ingested
if [ ! -f "data/embeddings/faiss.index" ]; then
    echo ""
    echo "📄 No RAG index found. Documents need to be ingested."
    echo "After the server starts, run:"
    echo ""
    echo "curl -X POST 'http://localhost:8000/ingest' \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"document_paths\": [\"data/documents/company_policy.txt\", \"data/documents/product_faq.txt\", \"data/documents/api_documentation.txt\"]}'"
    echo ""
fi

# Start the server
echo "✅ Starting server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

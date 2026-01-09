#!/bin/bash

# Setup Verification Script for AI Agent RAG System

echo "🔍 AI Agent RAG System - Setup Verification"
echo "==========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "1. Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $PYTHON_VERSION"
if [[ "$PYTHON_VERSION" > "3.11" ]]; then
    echo -e "   ${GREEN}✅ Python version OK${NC}"
else
    echo -e "   ${RED}❌ Python 3.11+ required${NC}"
fi
echo ""

# Check virtual environment
echo "2. Checking virtual environment..."
if [ -d "venv" ]; then
    echo -e "   ${GREEN}✅ Virtual environment exists${NC}"
else
    echo -e "   ${RED}❌ Virtual environment not found${NC}"
    echo "   Run: python3 -m venv venv"
fi
echo ""

# Check if venv is activated
echo "3. Checking if virtual environment is activated..."
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "   ${GREEN}✅ Virtual environment activated${NC}"
    echo "   Path: $VIRTUAL_ENV"
else
    echo -e "   ${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo "   Run: source venv/bin/activate"
fi
echo ""

# Check dependencies
echo "4. Checking Python packages..."
if [[ "$VIRTUAL_ENV" != "" ]]; then
    PACKAGES=("fastapi" "uvicorn" "openai" "langchain" "faiss" "pypdf" "azure-identity")
    for package in "${PACKAGES[@]}"; do
        if python -c "import $package" 2>/dev/null; then
            echo -e "   ${GREEN}✅ $package${NC}"
        else
            echo -e "   ${RED}❌ $package not installed${NC}"
        fi
    done
else
    echo -e "   ${YELLOW}⚠️  Activate venv first to check packages${NC}"
fi
echo ""

# Check .env file
echo "5. Checking environment configuration..."
if [ -f ".env" ]; then
    echo -e "   ${GREEN}✅ .env file exists${NC}"
    
    # Check for API keys
    if grep -q "AZURE_OPENAI_API_KEY=your-api-key" .env || grep -q "OPENAI_API_KEY=sk-" .env; then
        echo -e "   ${YELLOW}⚠️  API keys need to be configured${NC}"
        echo "   Edit .env and add your Azure OpenAI or OpenAI API key"
    else
        echo -e "   ${GREEN}✅ API keys appear to be configured${NC}"
    fi
else
    echo -e "   ${RED}❌ .env file not found${NC}"
    echo "   Run: cp .env.example .env"
fi
echo ""

# Check project structure
echo "6. Checking project structure..."
REQUIRED_DIRS=("app" "data/documents" "tests")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "   ${GREEN}✅ $dir/${NC}"
    else
        echo -e "   ${RED}❌ $dir/ missing${NC}"
    fi
done
echo ""

# Check sample documents
echo "7. Checking sample documents..."
DOCS=("data/documents/company_policy.txt" "data/documents/product_faq.txt" "data/documents/api_documentation.txt")
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "   ${GREEN}✅ $(basename $doc)${NC}"
    else
        echo -e "   ${RED}❌ $(basename $doc) missing${NC}"
    fi
done
echo ""

# Check scripts
echo "8. Checking executable scripts..."
SCRIPTS=("start.sh" "deploy_azure.sh" "deploy_azure_functions.sh")
for script in "${SCRIPTS[@]}"; do
    if [ -x "$script" ]; then
        echo -e "   ${GREEN}✅ $script (executable)${NC}"
    elif [ -f "$script" ]; then
        echo -e "   ${YELLOW}⚠️  $script (not executable)${NC}"
        echo "   Run: chmod +x $script"
    else
        echo -e "   ${RED}❌ $script missing${NC}"
    fi
done
echo ""

# Summary
echo "==========================================="
echo "📋 Setup Summary"
echo "==========================================="
echo ""

if [ -d "venv" ] && [ -f ".env" ] && [ -d "app" ]; then
    echo -e "${GREEN}✅ Basic setup complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Activate virtual environment: source venv/bin/activate"
    echo "2. Configure API keys in .env file"
    echo "3. Start the server: ./start.sh"
    echo "4. Ingest documents: curl -X POST http://localhost:8000/ingest ..."
    echo "5. Test the API: curl -X POST http://localhost:8000/ask ..."
    echo ""
    echo "📚 Documentation:"
    echo "   - README.md - Complete documentation"
    echo "   - QUICKSTART.md - Quick start guide"
    echo "   - PROJECT_SUMMARY.md - Project overview"
else
    echo -e "${RED}❌ Setup incomplete${NC}"
    echo ""
    echo "Please complete the setup steps above."
fi
echo ""

"""
FastAPI application - Main API implementation.
This implements Task 3: Backend API with FastAPI.
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.models import (
    QueryRequest,
    QueryResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse
)
from app.agent import AIAgent
from app.rag import RAGSystem

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
rag_system: RAGSystem = None
ai_agent: AIAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global rag_system, ai_agent
    
    # Startup
    logger.info("Starting AI Agent RAG System...")
    
    # Initialize RAG system
    rag_system = RAGSystem()
    
    # Try to load existing index
    if rag_system.load_index():
        logger.info("Loaded existing RAG index")
    else:
        logger.warning("No existing RAG index found. Use /ingest endpoint to add documents.")
    
    # Initialize AI agent with RAG system
    ai_agent = AIAgent(rag_system=rag_system)
    logger.info("AI Agent initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Agent RAG System...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    AI Agent with RAG (Retrieval-Augmented Generation) capabilities.
    
    Features:
    - Intelligent query routing (direct LLM or document search)
    - Tool calling (calculations, time, document search)
    - Session-based conversation memory
    - Document ingestion and semantic search
    """,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Agent RAG System API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat(),
        rag_initialized=rag_system.is_initialized if rag_system else False
    )


@app.post("/ask", response_model=QueryResponse, tags=["Agent"])
async def ask_question(request: QueryRequest):
    """
    Main endpoint to ask questions to the AI agent.
    
    The agent will:
    1. Analyze the query
    2. Decide whether to use tools (document search, calculator, etc.)
    3. Generate a response using LLM
    4. Return the answer with sources and metadata
    """
    try:
        if not ai_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent not initialized"
            )
        
        logger.info(f"Processing query: {request.query[:100]}... (session: {request.session_id})")
        
        # Process the query
        result = await ai_agent.process_query(
            query=request.query,
            session_id=request.session_id,
            use_tools=request.use_tools
        )
        
        # Check for errors
        if "error" in result:
            logger.error(f"Error processing query: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        logger.info(f"Query processed successfully (session: {request.session_id})")
        
        return QueryResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /ask endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@app.post("/ingest", response_model=IngestResponse, tags=["RAG"])
async def ingest_documents(request: IngestRequest):
    """
    Ingest documents into the RAG system.
    
    Processes documents, generates embeddings, and stores them in the vector database.
    """
    try:
        if not rag_system:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG system not initialized"
            )
        
        logger.info(f"Ingesting {len(request.document_paths)} documents")
        
        # Ingest documents
        result = rag_system.ingest_documents(request.document_paths)
        
        # Save the index
        rag_system.save_index()
        logger.info("RAG index saved successfully")
        
        return IngestResponse(
            status="success",
            total_documents=result["total_documents"],
            total_chunks=result["total_chunks"],
            message=f"Successfully ingested {result['total_documents']} documents with {result['total_chunks']} chunks"
        )
    
    except ValueError as e:
        logger.error(f"Validation error in /ingest: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in /ingest endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during ingestion: {str(e)}"
        )


@app.get("/sessions/{session_id}/history", tags=["Agent"])
async def get_session_history(session_id: str, limit: int = 10):
    """Get conversation history for a session."""
    try:
        if not ai_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent not initialized"
            )
        
        history = ai_agent.memory.get_history(session_id, limit)
        
        return {
            "session_id": session_id,
            "message_count": len(history),
            "messages": history
        }
    
    except Exception as e:
        logger.error(f"Error retrieving session history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.delete("/sessions/{session_id}", tags=["Agent"])
async def clear_session(session_id: str):
    """Clear a conversation session."""
    try:
        if not ai_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent not initialized"
            )
        
        ai_agent.memory.clear_session(session_id)
        
        return {
            "status": "success",
            "message": f"Session {session_id} cleared"
        }
    
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/search", tags=["RAG"])
async def search_documents(query: str, top_k: int = 3):
    """
    Search documents directly without using the agent.
    Useful for testing RAG functionality.
    """
    try:
        if not rag_system:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG system not initialized"
            )
        
        if not rag_system.is_initialized:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents have been ingested yet"
            )
        
        results = rag_system.search(query, top_k)
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /search endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred",
            "error": str(exc) if settings.environment == "development" else "Internal server error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )

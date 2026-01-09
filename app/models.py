"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class QueryRequest(BaseModel):
    """Request model for /ask endpoint."""
    query: str = Field(..., description="User's question or request", min_length=1)
    session_id: Optional[str] = Field(default="default", description="Session identifier for conversation memory")
    use_tools: Optional[bool] = Field(default=True, description="Whether to enable tool calling")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is our company's vacation policy?",
                "session_id": "user-123",
                "use_tools": True
            }
        }


class QueryResponse(BaseModel):
    """Response model for /ask endpoint."""
    answer: str = Field(..., description="AI agent's response")
    sources: List[str] = Field(default_factory=list, description="Sources used to generate the answer")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tools that were called")
    session_id: str = Field(..., description="Session identifier")
    timestamp: str = Field(..., description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "According to our company policy, employees receive 15 days of paid vacation per year...",
                "sources": ["company_policy.pdf", "hr_handbook.pdf"],
                "tool_calls": [
                    {
                        "tool": "search_documents",
                        "arguments": {"query": "vacation policy"},
                        "result": "Found 3 relevant documents"
                    }
                ],
                "session_id": "user-123",
                "timestamp": "2024-01-10T00:00:00"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    app_name: str
    version: str
    timestamp: str
    rag_initialized: bool


class IngestRequest(BaseModel):
    """Request model for document ingestion."""
    document_paths: List[str] = Field(..., description="Paths to documents to ingest")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_paths": [
                    "data/documents/company_policy.pdf",
                    "data/documents/faq.txt"
                ]
            }
        }


class IngestResponse(BaseModel):
    """Response model for document ingestion."""
    status: str
    total_documents: int
    total_chunks: int
    message: str

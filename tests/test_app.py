"""
Unit tests for the AI Agent RAG System.
"""
import pytest
from app.agent import AIAgent, AgentMemory, AgentTools
from app.rag import DocumentProcessor, RAGSystem
from app.config import settings


class TestAgentMemory:
    """Test the agent memory system."""
    
    def test_add_and_retrieve_message(self):
        """Test adding and retrieving messages."""
        memory = AgentMemory()
        session_id = "test-session"
        
        memory.add_message(session_id, "user", "Hello")
        memory.add_message(session_id, "assistant", "Hi there!")
        
        history = memory.get_history(session_id)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
    
    def test_session_isolation(self):
        """Test that sessions are isolated."""
        memory = AgentMemory()
        
        memory.add_message("session1", "user", "Message 1")
        memory.add_message("session2", "user", "Message 2")
        
        assert len(memory.get_history("session1")) == 1
        assert len(memory.get_history("session2")) == 1
        assert memory.get_history("session1")[0]["content"] == "Message 1"
    
    def test_clear_session(self):
        """Test clearing a session."""
        memory = AgentMemory()
        session_id = "test-session"
        
        memory.add_message(session_id, "user", "Test")
        assert len(memory.get_history(session_id)) == 1
        
        memory.clear_session(session_id)
        assert len(memory.get_history(session_id)) == 0


class TestAgentTools:
    """Test agent tools."""
    
    def test_get_current_time(self):
        """Test time retrieval tool."""
        result = AgentTools.get_current_time()
        assert "UTC" in result
        assert len(result) > 0
    
    def test_calculate_valid(self):
        """Test calculator with valid expression."""
        result = AgentTools.calculate("2 + 2")
        assert result == "4"
        
        result = AgentTools.calculate("10 * 5")
        assert result == "50"
    
    def test_calculate_invalid(self):
        """Test calculator with invalid expression."""
        result = AgentTools.calculate("import os")
        assert "Error" in result


class TestDocumentProcessor:
    """Test document processing."""
    
    def test_chunk_text(self):
        """Test text chunking."""
        processor = DocumentProcessor()
        text = "This is a test. " * 100  # Create long text
        
        chunks = processor.chunk_text(text, chunk_size=100, chunk_overlap=20)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 120 for chunk in chunks)  # Allow some overflow
    
    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        processor = DocumentProcessor()
        chunks = processor.chunk_text("")
        assert len(chunks) == 0


class TestRAGSystem:
    """Test RAG system components."""
    
    def test_rag_initialization(self):
        """Test RAG system initialization."""
        rag = RAGSystem()
        assert rag is not None
        assert not rag.is_initialized


# Integration tests would require API keys
# These are marked to skip if no API key is available

@pytest.mark.skipif(
    not settings.openai_api_key and not settings.azure_openai_api_key,
    reason="No API key configured"
)
class TestIntegration:
    """Integration tests (require API keys)."""
    
    @pytest.mark.asyncio
    async def test_agent_query(self):
        """Test agent query processing."""
        agent = AIAgent()
        result = await agent.process_query("What is 2+2?", session_id="test")
        
        assert "answer" in result
        assert result["answer"] is not None

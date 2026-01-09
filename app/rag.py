"""
RAG (Retrieval-Augmented Generation) System.
This implements Task 2: Document processing, embedding, and retrieval.
"""
from typing import List, Dict, Any, Optional
import os
import pickle
from pathlib import Path
import numpy as np
from openai import AzureOpenAI, OpenAI
import faiss
from PyPDF2 import PdfReader
from app.config import settings


class DocumentProcessor:
    """Process and chunk documents for RAG."""
    
    @staticmethod
    def load_pdf(file_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Error reading PDF {file_path}: {str(e)}")
    
    @staticmethod
    def load_text(file_path: str) -> str:
        """Load text from a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Error reading text file {file_path}: {str(e)}")
    
    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - chunk_overlap
        
        return [c for c in chunks if c]  # Remove empty chunks
    
    def process_document(
        self,
        file_path: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Process a document and return chunks with metadata."""
        chunk_size = chunk_size or settings.chunk_size
        chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        file_path = Path(file_path)
        
        # Load document based on type
        if file_path.suffix.lower() == '.pdf':
            text = self.load_pdf(str(file_path))
        elif file_path.suffix.lower() in ['.txt', '.md']:
            text = self.load_text(str(file_path))
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        # Chunk the text
        chunks = self.chunk_text(text, chunk_size, chunk_overlap)
        
        # Create chunk documents with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                "content": chunk,
                "source": file_path.name,
                "chunk_id": i,
                "metadata": {
                    "file_path": str(file_path),
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            })
        
        return documents


class EmbeddingGenerator:
    """Generate embeddings using OpenAI/Azure OpenAI."""
    
    def __init__(self):
        """Initialize the embedding generator."""
        # Use separate embedding endpoint/key if provided, otherwise fall back to main endpoint/key
        embedding_endpoint = settings.azure_openai_embedding_endpoint or settings.azure_openai_endpoint
        embedding_api_key = settings.azure_openai_embedding_api_key or settings.azure_openai_api_key
        
        if embedding_api_key and embedding_endpoint:
            self.client = AzureOpenAI(
                api_key=embedding_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=embedding_endpoint
            )
            self.model = settings.azure_openai_embedding_deployment
        elif settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = "text-embedding-ada-002"
        else:
            raise ValueError("No OpenAI API key configured for embeddings")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise ValueError(f"Error generating embedding: {str(e)}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        # Process in batches to avoid rate limits
        batch_size = 100
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            except Exception as e:
                raise ValueError(f"Error generating embeddings for batch {i}: {str(e)}")
        
        return embeddings


class FAISSVectorStore:
    """FAISS-based vector store for similarity search."""
    
    def __init__(self, dimension: int = 1536):
        """Initialize FAISS index."""
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents: List[Dict[str, Any]] = []
    
    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Add documents and their embeddings to the index."""
        if not documents or not embeddings:
            return
        
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")
        
        # Convert embeddings to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Add to FAISS index
        self.index.add(embeddings_array)
        
        # Store documents
        self.documents.extend(documents)
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if self.index.ntotal == 0:
            return []
        
        # Convert query to numpy array
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Search
        distances, indices = self.index.search(query_array, min(top_k, self.index.ntotal))
        
        # Prepare results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                result = self.documents[idx].copy()
                result['score'] = float(distances[0][i])
                results.append(result)
        
        return results
    
    def save(self, index_path: str, documents_path: str):
        """Save index and documents to disk."""
        faiss.write_index(self.index, index_path)
        with open(documents_path, 'wb') as f:
            pickle.dump(self.documents, f)
    
    def load(self, index_path: str, documents_path: str):
        """Load index and documents from disk."""
        if os.path.exists(index_path) and os.path.exists(documents_path):
            self.index = faiss.read_index(index_path)
            with open(documents_path, 'rb') as f:
                self.documents = pickle.load(f)
            return True
        return False


class RAGSystem:
    """Complete RAG system combining document processing, embedding, and retrieval."""
    
    def __init__(self):
        """Initialize the RAG system."""
        self.processor = DocumentProcessor()
        self.embedder = EmbeddingGenerator()
        self.vector_store = FAISSVectorStore()
        self.is_initialized = False
    
    def ingest_documents(self, document_paths: List[str]) -> Dict[str, Any]:
        """Ingest documents into the RAG system."""
        all_documents = []
        
        # Process all documents
        for doc_path in document_paths:
            try:
                chunks = self.processor.process_document(doc_path)
                all_documents.extend(chunks)
                print(f"Processed {doc_path}: {len(chunks)} chunks")
            except Exception as e:
                print(f"Error processing {doc_path}: {str(e)}")
        
        if not all_documents:
            raise ValueError("No documents were successfully processed")
        
        # Generate embeddings
        print(f"Generating embeddings for {len(all_documents)} chunks...")
        texts = [doc["content"] for doc in all_documents]
        embeddings = self.embedder.generate_embeddings(texts)
        
        # Add to vector store
        self.vector_store.add_documents(all_documents, embeddings)
        self.is_initialized = True
        
        return {
            "total_documents": len(document_paths),
            "total_chunks": len(all_documents),
            "status": "success"
        }
    
    def search(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for relevant documents."""
        if not self.is_initialized:
            return []
        
        top_k = top_k or settings.top_k_results
        
        # Generate query embedding
        query_embedding = self.embedder.generate_embedding(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, top_k)
        
        return results
    
    def save_index(self, base_path: str = "data/embeddings"):
        """Save the vector index to disk."""
        os.makedirs(base_path, exist_ok=True)
        index_path = os.path.join(base_path, "faiss.index")
        documents_path = os.path.join(base_path, "documents.pkl")
        self.vector_store.save(index_path, documents_path)
    
    def load_index(self, base_path: str = "data/embeddings") -> bool:
        """Load the vector index from disk."""
        index_path = os.path.join(base_path, "faiss.index")
        documents_path = os.path.join(base_path, "documents.pkl")
        
        if self.vector_store.load(index_path, documents_path):
            self.is_initialized = True
            return True
        return False

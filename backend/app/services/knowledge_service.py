import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from ..core.config import settings
from ..models.chat import KnowledgeDocument
from .file_processor import FileProcessor
import hashlib

class KnowledgeService:
    """Service for managing movie industry knowledge base and context retrieval."""
    
    def __init__(self):
        self.knowledge_base_path = Path(settings.knowledge_base_path)
        self.vector_db_path = Path(settings.vector_db_path)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB for vector storage
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.vector_db_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="movie_industry_knowledge",
            metadata={"description": "Movie industry knowledge base"}
        )
        
        # Initialize file processor
        self.file_processor = FileProcessor()
        
        # Load existing documents
        self.documents: Dict[str, KnowledgeDocument] = {}
        self._load_existing_documents()
    
    def _load_existing_documents(self):
        """Load existing documents from the knowledge base directory."""
        if not self.knowledge_base_path.exists():
            return
        
        for file_path in self.knowledge_base_path.rglob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract metadata from filename or create default
                category = self._extract_category_from_path(file_path)
                title = file_path.stem.replace('_', ' ').title()
                
                doc = KnowledgeDocument(
                    id=str(file_path),
                    title=title,
                    content=content,
                    category=category,
                    tags=[category]
                )
                
                self.documents[doc.id] = doc
                self._add_to_vector_db(doc)
                
            except Exception as e:
                print(f"Error loading document {file_path}: {e}")
    
    def _extract_category_from_path(self, file_path: Path) -> str:
        """Extract category from file path structure."""
        path_parts = file_path.parts
        
        # Look for category indicators in path
        for part in path_parts:
            part_lower = part.lower()
            if 'pre-production' in part_lower or 'preproduction' in part_lower:
                return 'pre-production'
            elif 'production' in part_lower:
                return 'production'
            elif 'post-production' in part_lower or 'postproduction' in part_lower:
                return 'post-production'
        
        # Default to production if no category found
        return 'production'
    
    def _add_to_vector_db(self, document: KnowledgeDocument):
        """Add document to vector database for semantic search."""
        try:
            # Create chunks of the document for better retrieval
            chunks = self._chunk_text(document.content, chunk_size=1000)
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document.id}_chunk_{i}"
                self.collection.add(
                    documents=[chunk],
                    metadatas=[{
                        "document_id": document.id,
                        "title": document.title,
                        "category": document.category,
                        "chunk_index": i
                    }],
                    ids=[chunk_id]
                )
        except Exception as e:
            print(f"Error adding document to vector DB: {e}")
    
    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into chunks for vector storage."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    async def add_document(self, title: str, content: str, category: str, tags: List[str] = None) -> KnowledgeDocument:
        """Add a new document to the knowledge base."""
        # Generate unique ID
        doc_id = hashlib.md5(f"{title}{content}".encode()).hexdigest()
        
        doc = KnowledgeDocument(
            id=doc_id,
            title=title,
            content=content,
            category=category,
            tags=tags or [category]
        )
        
        self.documents[doc_id] = doc
        self._add_to_vector_db(doc)
        
        return doc
    
    async def search_context(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant context based on user query."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=max_results,
                include=["metadatas", "distances"]
            )
            
            context_results = []
            for i, metadata in enumerate(results['metadatas'][0]):
                doc_id = metadata['document_id']
                if doc_id in self.documents:
                    doc = self.documents[doc_id]
                    context_results.append({
                        'title': doc.title,
                        'category': doc.category,
                        'content': doc.content,
                        'relevance_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                    })
            
            return context_results
            
        except Exception as e:
            print(f"Error searching context: {e}")
            return []
    
    async def get_documents_by_category(self, category: str) -> List[KnowledgeDocument]:
        """Get all documents in a specific category."""
        return [doc for doc in self.documents.values() if doc.category == category]
    
    async def get_all_documents(self) -> List[KnowledgeDocument]:
        """Get all documents in the knowledge base."""
        return list(self.documents.values())
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the knowledge base."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            # Note: Vector DB cleanup would need more sophisticated handling
            return True
        return False
    
    async def process_uploaded_file(self, file_content: bytes, filename: str, category: str) -> List[KnowledgeDocument]:
        """
        Process an uploaded file and add it to the knowledge base.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            category: Document category
            
        Returns:
            List of processed KnowledgeDocument objects
        """
        try:
            # Process the file
            documents = await self.file_processor.process_file(file_content, filename, category)
            
            # Add each document to the knowledge base
            for doc in documents:
                self.documents[doc.id] = doc
                self._add_to_vector_db(doc)
            
            return documents
            
        except Exception as e:
            raise Exception(f"Error processing uploaded file: {str(e)}")
    
    def get_supported_file_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return self.file_processor.get_supported_formats()
    
    def get_file_size_limit(self) -> int:
        """Get maximum file size limit."""
        return self.file_processor.get_file_size_limit()
    
    def validate_uploaded_file(self, filename: str, file_size: int) -> tuple[bool, str]:
        """Validate uploaded file before processing."""
        return self.file_processor.validate_file(filename, file_size) 
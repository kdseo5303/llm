from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from ..models.chat import KnowledgeDocument
from ..services.knowledge_service import KnowledgeService
import uuid

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# Initialize service
knowledge_service = KnowledgeService()

@router.get("/", response_model=List[KnowledgeDocument])
async def get_all_documents():
    """Get all documents in the knowledge base."""
    try:
        return await knowledge_service.get_all_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

@router.get("/category/{category}", response_model=List[KnowledgeDocument])
async def get_documents_by_category(category: str):
    """Get documents by category (pre-production, production, post-production)."""
    try:
        return await knowledge_service.get_documents_by_category(category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents by category: {str(e)}")

@router.post("/", response_model=KnowledgeDocument)
async def add_document(
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    tags: Optional[str] = Form(None)
):
    """
    Add a new document to the knowledge base.
    
    Args:
        title: Document title
        content: Document content
        category: Document category (pre-production, production, post-production)
        tags: Comma-separated tags (optional)
    """
    try:
        # Parse tags if provided
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
        
        # Validate category
        valid_categories = ["pre-production", "production", "post-production"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )
        
        document = await knowledge_service.add_document(
            title=title,
            content=content,
            category=category,
            tags=tag_list
        )
        
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding document: {str(e)}")

@router.post("/upload-text")
async def upload_text_file(
    file: UploadFile = File(...),
    category: str = Form(...),
    tags: Optional[str] = Form(None)
):
    """
    Upload a text file to the knowledge base.
    
    Args:
        file: Text file to upload
        category: Document category
        tags: Comma-separated tags (optional)
    """
    try:
        # Validate file type
        if not file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="Only .txt files are supported")
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Parse tags if provided
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
        
        # Validate category
        valid_categories = ["pre-production", "production", "post-production"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )
        
        # Use filename as title (remove extension)
        title = file.filename.rsplit('.', 1)[0].replace('_', ' ').title()
        
        document = await knowledge_service.add_document(
            title=title,
            content=content_str,
            category=category,
            tags=tag_list
        )
        
        return {
            "message": "Document uploaded successfully",
            "document": document
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the knowledge base."""
    try:
        success = await knowledge_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.get("/search")
async def search_documents(query: str, max_results: int = 5):
    """
    Search for documents based on a query.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
    """
    try:
        results = await knowledge_service.search_context(query, max_results)
        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@router.get("/stats")
async def get_knowledge_stats():
    """Get statistics about the knowledge base."""
    try:
        all_docs = await knowledge_service.get_all_documents()
        
        # Count by category
        category_counts = {}
        for doc in all_docs:
            category_counts[doc.category] = category_counts.get(doc.category, 0) + 1
        
        # Calculate total content length
        total_content_length = sum(len(doc.content) for doc in all_docs)
        
        return {
            "total_documents": len(all_docs),
            "category_distribution": category_counts,
            "total_content_length": total_content_length,
            "average_document_length": total_content_length / len(all_docs) if all_docs else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}") 
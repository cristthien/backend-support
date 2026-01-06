"""
Document repository for database operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.document import Document
from typing import Optional, List


async def create_document(
    db: AsyncSession,
    user_id: int,
    title: str,
    body: str,
    doc_type: str = "program",
    academic_year: Optional[str] = None
) -> Document:
    """Create a new document"""
    doc = Document(
        user_id=user_id,
        title=title,
        type=doc_type,
        academic_year=academic_year,
        body=body
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def get_documents(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 10
) -> tuple[List[Document], int]:
    """Get user's documents with pagination"""
    # Get total count
    count_result = await db.execute(
        select(func.count(Document.id)).select_from(Document).where(Document.user_id == user_id)
    )
    total = count_result.scalar()
    
    # Get documents
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()
    
    return documents, total


async def get_document_by_id(db: AsyncSession, doc_id: int, user_id: int) -> Optional[Document]:
    """Get document by ID (ensures user owns the document)"""
    result = await db.execute(
        select(Document)
        .where(Document.id == doc_id)
        .where(Document.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_document(
    db: AsyncSession,
    doc: Document,
    title: Optional[str] = None,
    body: Optional[str] = None,
    doc_type: Optional[str] = None,
    academic_year: Optional[str] = None
) -> Document:
    """Update document"""
    if title is not None:
        doc.title = title
    if body is not None:
        doc.body = body
    if doc_type is not None:
        doc.type = doc_type
    if academic_year is not None:
        doc.academic_year = academic_year
    
    await db.commit()
    await db.refresh(doc)
    return doc


async def delete_document(db: AsyncSession, doc: Document) -> None:
    """Delete document"""
    await db.delete(doc)
    await db.commit()


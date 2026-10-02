from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import AsyncSessionLocal
from models import Document
from elastic import search_in_elastic, delete_document_from_elastic

app = FastAPI(title="Document Search Service")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@app.get("/search")
async def search_documents(q: str, db: AsyncSession = Depends(get_db)):

    if not q.strip():
        return []


    doc_ids = await search_in_elastic(query_text=q, limit=20)

    if not doc_ids:
        return []


    stmt = (
        select(Document)
        .where(Document.id.in_(doc_ids))
        .order_by(Document.created_date.desc())  # Сортировка по дате создания
    )
    result = await db.execute(stmt)
    documents = result.scalars().all()

    return documents


@app.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db)):


    stmt = select(Document).where(Document.id == doc_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Документ не найден"
        )


    await db.delete(doc)
    await db.commit()

    await delete_document_from_elastic(doc_id=doc_id)

    return None

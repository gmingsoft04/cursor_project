from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Customer
from ..schemas import (
    SaveSelectedRequest,
    SearchRequest,
    SearchResult,
    SearchResultItem,
)
from ..services.email_search import EmailSearchService

router = APIRouter(prefix="/api/search", tags=["search"])

_service = EmailSearchService()


@router.get("/providers")
def providers():
    return {"providers": _service.available_providers()}


@router.post("", response_model=SearchResult)
async def search(payload: SearchRequest, db: Session = Depends(get_db)):
    try:
        result = await _service.search(payload.keyword, payload.provider, payload.limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"搜索失败: {exc}")

    items_out = []
    if result.items:
        existing_emails = {
            row[0]
            for row in db.execute(
                select(Customer.email).where(Customer.email.in_([i.email for i in result.items]))
            )
        }
    else:
        existing_emails = set()

    for it in result.items:
        items_out.append(
            SearchResultItem(
                email=it.email,
                name=it.name,
                company=it.company,
                position=it.position,
                country=it.country,
                website=it.website,
                confidence=it.confidence,
                source=it.source,
                keyword=it.keyword or payload.keyword,
                already_exists=it.email in existing_emails,
            )
        )

    return SearchResult(
        provider=result.provider,
        keyword=result.keyword,
        items=items_out,
        notice=result.notice,
    )


@router.post("/save")
def save_selected(payload: SaveSelectedRequest, db: Session = Depends(get_db)):
    inserted, skipped = 0, 0
    for it in payload.items:
        existing = db.scalar(select(Customer).where(Customer.email == it.email))
        if existing:
            skipped += 1
            continue
        c = Customer(
            email=it.email,
            name=it.name,
            company=it.company,
            position=it.position,
            country=it.country,
            website=it.website,
            source=it.source,
            keyword=it.keyword,
            confidence=it.confidence,
        )
        db.add(c)
        inserted += 1
    db.commit()
    return {"inserted": inserted, "skipped": skipped}

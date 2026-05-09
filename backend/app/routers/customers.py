from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Customer
from ..schemas import (
    CustomerBulkImport,
    CustomerCreate,
    CustomerListOut,
    CustomerOut,
    CustomerUpdate,
)

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("", response_model=CustomerListOut)
def list_customers(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="搜索关键字（邮箱/姓名/公司/国家）"),
    unsubscribed: Optional[bool] = None,
    country: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
):
    stmt = select(Customer)
    count_stmt = select(func.count(Customer.id))
    filters = []
    if q:
        like = f"%{q}%"
        filters.append(
            or_(
                Customer.email.ilike(like),
                Customer.name.ilike(like),
                Customer.company.ilike(like),
                Customer.country.ilike(like),
            )
        )
    if unsubscribed is not None:
        filters.append(Customer.unsubscribed == unsubscribed)
    if country:
        filters.append(Customer.country == country)
    if keyword:
        filters.append(Customer.keyword == keyword)

    if filters:
        for f in filters:
            stmt = stmt.where(f)
            count_stmt = count_stmt.where(f)

    total = db.execute(count_stmt).scalar_one()
    stmt = stmt.order_by(Customer.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(stmt).scalars().all()
    return CustomerListOut(items=items, total=total)


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Customer).where(Customer.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="该邮箱已存在")
    obj = Customer(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/bulk", response_model=dict)
def bulk_import(payload: CustomerBulkImport, db: Session = Depends(get_db)):
    inserted, updated, skipped = 0, 0, 0
    for item in payload.items:
        existing = db.scalar(select(Customer).where(Customer.email == item.email))
        if existing:
            # 仅在原字段为空时回填
            data = item.model_dump(exclude_unset=True)
            changed = False
            for k, v in data.items():
                if k == "email":
                    continue
                if v and not getattr(existing, k, None):
                    setattr(existing, k, v)
                    changed = True
            if changed:
                updated += 1
            else:
                skipped += 1
        else:
            db.add(Customer(**item.model_dump()))
            inserted += 1
    db.commit()
    return {"inserted": inserted, "updated": updated, "skipped": skipped}


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    obj = db.get(Customer, customer_id)
    if not obj:
        raise HTTPException(status_code=404, detail="客户不存在")
    return obj


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)):
    obj = db.get(Customer, customer_id)
    if not obj:
        raise HTTPException(status_code=404, detail="客户不存在")
    data = payload.model_dump(exclude_unset=True)
    if "unsubscribed" in data:
        if data["unsubscribed"] and not obj.unsubscribed:
            obj.unsubscribed_at = datetime.utcnow()
        elif data["unsubscribed"] is False:
            obj.unsubscribed_at = None
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    obj = db.get(Customer, customer_id)
    if not obj:
        raise HTTPException(status_code=404, detail="客户不存在")
    db.delete(obj)
    db.commit()
    return None


@router.get("/_/stats", response_model=dict)
def stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(Customer.id))) or 0
    unsubscribed = db.scalar(
        select(func.count(Customer.id)).where(Customer.unsubscribed == True)  # noqa: E712
    ) or 0
    active = total - unsubscribed
    return {"total": total, "active": active, "unsubscribed": unsubscribed}

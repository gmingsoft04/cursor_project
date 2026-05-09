from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Template
from ..schemas import TemplateCreate, TemplateOut, TemplateUpdate

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=List[TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return db.execute(select(Template).order_by(Template.id.asc())).scalars().all()


@router.post("", response_model=TemplateOut, status_code=201)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)):
    obj = Template(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{tpl_id}", response_model=TemplateOut)
def get_template(tpl_id: int, db: Session = Depends(get_db)):
    obj = db.get(Template, tpl_id)
    if not obj:
        raise HTTPException(404, detail="模板不存在")
    return obj


@router.patch("/{tpl_id}", response_model=TemplateOut)
def update_template(tpl_id: int, payload: TemplateUpdate, db: Session = Depends(get_db)):
    obj = db.get(Template, tpl_id)
    if not obj:
        raise HTTPException(404, detail="模板不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{tpl_id}", status_code=204)
def delete_template(tpl_id: int, db: Session = Depends(get_db)):
    obj = db.get(Template, tpl_id)
    if not obj:
        raise HTTPException(404, detail="模板不存在")
    db.delete(obj)
    db.commit()
    return None

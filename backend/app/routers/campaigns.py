import asyncio
import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import SessionLocal, get_db
from ..models import Campaign, Customer, EmailLog, Template
from ..schemas import (
    CampaignDetail,
    CampaignOut,
    CampaignSendRequest,
    EmailLogOut,
)
from ..services.mailer import (
    Mailer,
    build_render_context,
    ensure_unsubscribe_link,
    render_template,
)
from ..services.tokens import build_unsubscribe_url

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("", response_model=List[CampaignOut])
def list_campaigns(db: Session = Depends(get_db)):
    return db.execute(select(Campaign).order_by(Campaign.created_at.desc())).scalars().all()


@router.get("/{cid}", response_model=CampaignDetail)
def get_campaign(cid: int, db: Session = Depends(get_db)):
    obj = db.get(Campaign, cid)
    if not obj:
        raise HTTPException(404, "群发任务不存在")
    logs = (
        db.execute(select(EmailLog).where(EmailLog.campaign_id == cid).order_by(EmailLog.id.asc()))
        .scalars()
        .all()
    )
    detail = CampaignDetail.model_validate(obj)
    detail.logs = [EmailLogOut.model_validate(l) for l in logs]
    return detail


def _resolve_subject_body(
    db: Session, payload: CampaignSendRequest
) -> tuple[str, str, bool, Optional[Template]]:
    template = None
    if payload.template_id:
        template = db.get(Template, payload.template_id)
        if not template:
            raise HTTPException(400, "选择的模板不存在")
    subject = payload.subject or (template.subject if template else None)
    body = payload.body or (template.body if template else None)
    is_html = payload.is_html if payload.is_html is not None else (template.is_html if template else True)
    if not subject or not body:
        raise HTTPException(400, "缺少 subject/body 或 template_id")
    return subject, body, bool(is_html), template


def _resolve_recipients(db: Session, payload: CampaignSendRequest) -> List[Customer]:
    if payload.send_all_active:
        return list(
            db.execute(
                select(Customer).where(Customer.unsubscribed == False)  # noqa: E712
            ).scalars()
        )
    if not payload.customer_ids:
        return []
    return list(
        db.execute(select(Customer).where(Customer.id.in_(payload.customer_ids))).scalars()
    )


@router.post("/preview")
def preview(payload: CampaignSendRequest, db: Session = Depends(get_db)):
    subject_tpl, body_tpl, is_html, _ = _resolve_subject_body(db, payload)
    recipients = _resolve_recipients(db, payload)
    if not recipients:
        raise HTTPException(400, "未选择任何收件人")
    sample = recipients[0]
    s = get_settings()
    unsub_url = build_unsubscribe_url(s.app_base_url, sample.id, sample.email)
    ctx = build_render_context(sample, unsub_url, s.smtp_from_name or s.smtp_user or "Sender")
    rendered_subject = render_template(subject_tpl, ctx)
    rendered_body = render_template(body_tpl, ctx)
    rendered_body = ensure_unsubscribe_link(rendered_body, is_html, unsub_url)
    will_skip = sum(1 for c in recipients if c.unsubscribed)
    will_send = len(recipients) - will_skip
    return {
        "sample_to": sample.email,
        "subject": rendered_subject,
        "body": rendered_body,
        "is_html": is_html,
        "total": len(recipients),
        "will_send": will_send,
        "will_skip_unsubscribed": will_skip,
    }


@router.post("/send", response_model=CampaignOut)
async def send_campaign(payload: CampaignSendRequest, db: Session = Depends(get_db)):
    subject_tpl, body_tpl, is_html, template = _resolve_subject_body(db, payload)
    recipients = _resolve_recipients(db, payload)
    if not recipients:
        raise HTTPException(400, "未选择任何收件人")

    mailer = Mailer()
    if not mailer.configured:
        raise HTTPException(400, "SMTP 未配置，请在 .env 中填写 SMTP_* 设置后重启后端")

    name = payload.name or f"Campaign {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    campaign = Campaign(
        name=name,
        template_id=template.id if template else None,
        subject=subject_tpl,
        body=body_tpl,
        is_html=is_html,
        total=len(recipients),
        status="running",
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    s = get_settings()
    succeeded = failed = skipped = 0

    for idx, customer in enumerate(recipients):
        if customer.unsubscribed:
            log = EmailLog(
                campaign_id=campaign.id,
                customer_id=customer.id,
                to_email=customer.email,
                subject=subject_tpl,
                status="skipped",
                error="customer unsubscribed",
            )
            db.add(log)
            skipped += 1
            continue

        # 同步发送（每封邮件之间节流），用 to_thread 避免阻塞事件循环
        result = await asyncio.to_thread(
            mailer.send_to_customer, customer, subject_tpl, body_tpl, is_html
        )
        log = EmailLog(
            campaign_id=campaign.id,
            customer_id=customer.id,
            to_email=customer.email,
            subject=subject_tpl,
            status="success" if result.ok else "failed",
            error=None if result.ok else result.error,
        )
        db.add(log)
        if result.ok:
            succeeded += 1
        else:
            failed += 1

        # 节流，避免被反垃圾系统拦截
        if idx < len(recipients) - 1 and s.send_batch_interval > 0:
            await asyncio.sleep(s.send_batch_interval)

    campaign.succeeded = succeeded
    campaign.failed = failed
    campaign.skipped = skipped
    campaign.status = "completed"
    campaign.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(campaign)
    return campaign

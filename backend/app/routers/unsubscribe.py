from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Customer
from ..services.tokens import verify_unsubscribe_token

router = APIRouter(tags=["unsubscribe"])


_PAGE_OK = """<!doctype html>
<html lang="zh">
<head><meta charset="utf-8"><title>退订成功 / Unsubscribed</title>
<style>
body{{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#f6f7fb;margin:0;padding:0}}
.box{{max-width:520px;margin:80px auto;background:#fff;padding:40px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.06)}}
h1{{color:#0f766e;margin-top:0}}
.email{{color:#666;font-family:ui-monospace,Menlo,monospace;background:#f1f5f9;padding:6px 10px;border-radius:6px;display:inline-block}}
</style></head>
<body><div class="box">
<h1>退订成功 / You have been unsubscribed</h1>
<p>您的邮箱 <span class="email">{email}</span> 已从我们的邮件列表中移除，今后将不会再收到我们的开发信。</p>
<p>Your email has been successfully removed from our mailing list. You will no longer receive marketing emails from us.</p>
</div></body></html>
"""

_PAGE_INVALID = """<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><title>无效的退订链接</title>
<style>body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#f6f7fb}}.box{{max-width:520px;margin:80px auto;background:#fff;padding:40px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.06)}}</style>
</head><body><div class="box"><h1>链接无效 / Invalid link</h1>
<p>退订链接已失效或被篡改。如需退订，请回复邮件告知我们。</p></div></body></html>
"""


@router.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_get(token: str = Query(...), db: Session = Depends(get_db)):
    data = verify_unsubscribe_token(token)
    if not data:
        return HTMLResponse(_PAGE_INVALID, status_code=400)
    customer = db.get(Customer, data.get("id"))
    if not customer or customer.email.lower() != str(data.get("email", "")).lower():
        return HTMLResponse(_PAGE_INVALID, status_code=400)
    if not customer.unsubscribed:
        customer.unsubscribed = True
        customer.unsubscribed_at = datetime.utcnow()
        db.commit()
    return HTMLResponse(_PAGE_OK.format(email=customer.email))


@router.post("/api/unsubscribe")
def unsubscribe_post(token: str, db: Session = Depends(get_db)):
    data = verify_unsubscribe_token(token)
    if not data:
        return JSONResponse({"ok": False, "error": "invalid token"}, status_code=400)
    customer = db.get(Customer, data.get("id"))
    if not customer:
        return JSONResponse({"ok": False, "error": "customer not found"}, status_code=404)
    if not customer.unsubscribed:
        customer.unsubscribed = True
        customer.unsubscribed_at = datetime.utcnow()
        db.commit()
    return {"ok": True, "email": customer.email}

"""SMTP 邮件发送 + 模板渲染（含退订链接注入）"""

from __future__ import annotations

import asyncio
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional

from jinja2 import Environment, BaseLoader, select_autoescape

from ..config import get_settings
from ..models import Customer
from .tokens import build_unsubscribe_url


@dataclass
class SendResult:
    ok: bool
    error: Optional[str] = None


_jinja_env = Environment(loader=BaseLoader(), autoescape=select_autoescape(["html", "xml"]))


def render_template(template_text: str, context: dict) -> str:
    """渲染模板，未知变量用空串占位以避免崩溃"""
    template = _jinja_env.from_string(template_text or "")
    safe_ctx = {**context}
    return template.render(**safe_ctx)


def build_render_context(customer: Customer, unsubscribe_url: str, sender_name: str) -> dict:
    return {
        "name": customer.name or "there",
        "first_name": (customer.name or "there").split(" ")[0],
        "email": customer.email,
        "company": customer.company or "your company",
        "country": customer.country or "",
        "position": customer.position or "",
        "website": customer.website or "",
        "sender_name": sender_name,
        "unsubscribe_url": unsubscribe_url,
    }


def ensure_unsubscribe_link(body: str, is_html: bool, unsubscribe_url: str) -> str:
    """如果用户模板里没有引用退订链接，则自动追加，确保合规"""
    if "{{unsubscribe_url}}" in body or "{{ unsubscribe_url }}" in body:
        return body
    if "unsubscribe" in body.lower() and unsubscribe_url in body:
        return body
    if is_html:
        footer = (
            f'<hr style="margin-top:24px;border:none;border-top:1px solid #eee;">'
            f'<p style="color:#888;font-size:12px;">如不希望再收到此类邮件，'
            f'请<a href="{unsubscribe_url}">点此退订</a>（Unsubscribe）。</p>'
        )
        return body + footer
    else:
        return body + f"\n\n--\nUnsubscribe: {unsubscribe_url}\n"


class Mailer:
    def __init__(self):
        self.settings = get_settings()

    @property
    def configured(self) -> bool:
        s = self.settings
        return bool(s.smtp_host and s.smtp_user and s.smtp_password and s.smtp_from_email)

    def _send_sync(self, to_email: str, subject: str, body: str, is_html: bool) -> SendResult:
        s = self.settings
        if not self.configured:
            return SendResult(ok=False, error="SMTP 未配置，请在 .env 或设置页填写 SMTP 信息")

        msg = EmailMessage()
        from_name = s.smtp_from_name or s.smtp_user
        msg["From"] = formataddr((from_name, s.smtp_from_email))
        msg["To"] = to_email
        msg["Subject"] = subject

        if is_html:
            msg.set_content("此邮件为 HTML 格式，请使用支持 HTML 的客户端查看。")
            msg.add_alternative(body, subtype="html")
        else:
            msg.set_content(body)

        try:
            if s.smtp_port == 465:
                ctx = ssl.create_default_context()
                with smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, context=ctx, timeout=30) as smtp:
                    smtp.login(s.smtp_user, s.smtp_password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=30) as smtp:
                    smtp.ehlo()
                    if s.smtp_use_tls:
                        smtp.starttls(context=ssl.create_default_context())
                        smtp.ehlo()
                    smtp.login(s.smtp_user, s.smtp_password)
                    smtp.send_message(msg)
            return SendResult(ok=True)
        except Exception as exc:  # noqa: BLE001
            return SendResult(ok=False, error=str(exc))

    async def send(self, to_email: str, subject: str, body: str, is_html: bool) -> SendResult:
        return await asyncio.to_thread(self._send_sync, to_email, subject, body, is_html)

    def send_to_customer(
        self, customer: Customer, subject_tpl: str, body_tpl: str, is_html: bool
    ) -> SendResult:
        s = self.settings
        unsub_url = build_unsubscribe_url(s.app_base_url, customer.id, customer.email)
        ctx = build_render_context(customer, unsub_url, s.smtp_from_name or s.smtp_user)
        try:
            subject = render_template(subject_tpl, ctx)
            body = render_template(body_tpl, ctx)
        except Exception as exc:  # noqa: BLE001
            return SendResult(ok=False, error=f"模板渲染失败: {exc}")
        body = ensure_unsubscribe_link(body, is_html, unsub_url)
        return self._send_sync(customer.email, subject, body, is_html)

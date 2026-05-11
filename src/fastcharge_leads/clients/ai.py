"""AI adapters for generating personalized outreach email drafts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .http import JsonHttpClient


@dataclass(frozen=True, slots=True)
class GeneratedEmail:
    subject: str
    body: str
    model: str
    raw_response: str | None = None


class OutreachEmailGenerator:
    def generate(self, context: dict[str, Any]) -> GeneratedEmail:
        raise NotImplementedError


class OpenAICompatibleEmailGenerator(OutreachEmailGenerator):
    """Generate email drafts using an OpenAI-compatible chat completions API."""

    def __init__(
        self,
        *,
        api_key: str,
        api_base: str,
        model: str,
        http: JsonHttpClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.http = http or JsonHttpClient()

    def generate(self, context: dict[str, Any]) -> GeneratedEmail:
        prompt = _build_prompt(context)
        data = self.http.request_json(
            "POST",
            f"{self.api_base}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json_body={
                "model": self.model,
                "temperature": 0.45,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a senior B2B foreign trade sales copywriter. "
                            "Write concise, compliant, personalized cold outreach emails. "
                            "Return only JSON with keys subject and body."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
        )
        content = _extract_message(data)
        parsed = _parse_json_object(content)
        subject = str(parsed.get("subject") or "").strip()
        body = str(parsed.get("body") or "").strip()
        if not subject or not body:
            fallback = LocalTemplateEmailGenerator(model=f"fallback-after-{self.model}").generate(context)
            return GeneratedEmail(fallback.subject, fallback.body, fallback.model, raw_response=content)
        return GeneratedEmail(subject=subject, body=body, model=self.model, raw_response=content)


class LocalTemplateEmailGenerator(OutreachEmailGenerator):
    """Deterministic fallback generator used when no AI API key is configured."""

    def __init__(self, model: str = "local-template") -> None:
        self.model = model

    def generate(self, context: dict[str, Any]) -> GeneratedEmail:
        company = context.get("company_name") or "your company"
        contact = context.get("recipient_name") or "there"
        product = context.get("product_interest") or "phone fast chargers and fast charging cables"
        country = context.get("country") or "your market"
        signals = context.get("signals") or []
        signal_line = f" I noticed your business is related to {signals[0]}." if signals else ""
        language = str(context.get("language") or "English").lower()
        if "chinese" in language or "中文" in language:
            subject = f"关于{product}的供应合作"
            body = (
                f"{contact}，您好，\n\n"
                f"我关注到 {company} 在 {country} 市场有手机配件相关业务。{signal_line}\n"
                f"我们专注供应 {product}，可支持 OEM/ODM、稳定交期和适合批发/零售渠道的包装方案。\n\n"
                "如果您近期在评估新的快充头或快充线供应商，我可以发一份产品目录、认证资料和报价区间供您参考。\n\n"
                "您看本周是否方便简单沟通一下？\n\n"
                "Best regards,\nFastCharge Sales"
            )
            return GeneratedEmail(subject=subject, body=body, model=self.model)

        subject = f"{product} supply for {company}"
        body = (
            f"Hi {contact},\n\n"
            f"I noticed {company} serves customers in {country}.{signal_line}\n\n"
            f"We manufacture and supply {product}, including options for OEM/ODM, retail packaging, and stable bulk delivery. "
            "Our range is a good fit for mobile accessory importers, distributors, wholesalers, and ecommerce sellers.\n\n"
            "If you are reviewing new suppliers, I can send a concise catalog, certification details, and target pricing for your market.\n\n"
            "Would it be useful if I shared a shortlist of our best-selling fast charging products?\n\n"
            "Best regards,\nFastCharge Sales"
        )
        return GeneratedEmail(subject=subject, body=body, model=self.model)


def _build_prompt(context: dict[str, Any]) -> str:
    return (
        "Generate one cold outreach email for a foreign trade sales team selling phone fast chargers, "
        "GaN chargers, USB-C PD chargers, and fast charging cables.\n"
        "Requirements:\n"
        "- Language: {language}\n"
        "- Keep it under 160 words unless Chinese is requested.\n"
        "- Mention one relevant business signal if available.\n"
        "- Do not invent certifications, prices, customer names, or partnerships.\n"
        "- Avoid spammy language and excessive punctuation.\n"
        "- End with a low-friction question.\n\n"
        "Lead context JSON:\n{context_json}"
    ).format(
        language=context.get("language") or "English",
        context_json=json.dumps(context, ensure_ascii=False, indent=2, default=str),
    )


def _extract_message(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return str(message.get("content") or "")


def _parse_json_object(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.S)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

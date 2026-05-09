"""退订 token 工具：基于 itsdangerous 进行签名/验签"""

from itsdangerous import URLSafeSerializer, BadSignature

from ..config import get_settings


def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().secret_key, salt="unsubscribe")


def make_unsubscribe_token(customer_id: int, email: str) -> str:
    return _serializer().dumps({"id": customer_id, "email": email})


def verify_unsubscribe_token(token: str) -> dict | None:
    try:
        return _serializer().loads(token)
    except BadSignature:
        return None


def build_unsubscribe_url(base_url: str, customer_id: int, email: str) -> str:
    token = make_unsubscribe_token(customer_id, email)
    base = base_url.rstrip("/")
    return f"{base}/unsubscribe?token={token}"

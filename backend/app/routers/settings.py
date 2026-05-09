from fastapi import APIRouter

from ..config import get_settings
from ..schemas import SettingsOut
from ..services.email_search import EmailSearchService
from ..services.mailer import Mailer

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_app_settings():
    s = get_settings()
    mailer = Mailer()
    search = EmailSearchService()
    return SettingsOut(
        app_name=s.app_name,
        app_base_url=s.app_base_url,
        smtp_configured=mailer.configured,
        smtp_from_email=s.smtp_from_email or None,
        providers_available=search.available_providers(),
    )

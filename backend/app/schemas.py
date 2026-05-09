from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------- Customer ----------
class CustomerBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None
    keyword: Optional[str] = None
    notes: Optional[str] = None
    confidence: Optional[int] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None
    keyword: Optional[str] = None
    notes: Optional[str] = None
    confidence: Optional[int] = None
    unsubscribed: Optional[bool] = None


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    unsubscribed: bool
    unsubscribed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CustomerListOut(BaseModel):
    items: List[CustomerOut]
    total: int


class CustomerBulkImport(BaseModel):
    items: List[CustomerCreate]


# ---------- Template ----------
class TemplateBase(BaseModel):
    name: str
    subject: str
    body: str
    description: Optional[str] = None
    is_html: bool = True


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    description: Optional[str] = None
    is_html: Optional[bool] = None


class TemplateOut(TemplateBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


# ---------- Search ----------
class SearchRequest(BaseModel):
    keyword: str = Field(..., description="关键字或域名，如 'phone charger importer USA' 或 'example.com'")
    provider: Optional[str] = Field(None, description="hunter / serpapi / demo；留空则按优先级自动选择")
    limit: int = 20


class SearchResultItem(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    confidence: Optional[int] = None
    source: str
    keyword: Optional[str] = None
    already_exists: bool = False


class SearchResult(BaseModel):
    provider: str
    keyword: str
    items: List[SearchResultItem]
    notice: Optional[str] = None


class SaveSelectedRequest(BaseModel):
    items: List[SearchResultItem]


# ---------- Campaign ----------
class CampaignSendRequest(BaseModel):
    name: Optional[str] = None
    template_id: Optional[int] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    is_html: bool = True
    customer_ids: Optional[List[int]] = None
    send_all_active: bool = False


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    subject: str
    is_html: bool
    total: int
    succeeded: int
    failed: int
    skipped: int
    status: str
    created_at: datetime
    finished_at: Optional[datetime] = None


class EmailLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    campaign_id: Optional[int]
    customer_id: Optional[int]
    to_email: str
    subject: str
    status: str
    error: Optional[str]
    sent_at: datetime


class CampaignDetail(CampaignOut):
    logs: List[EmailLogOut] = []


# ---------- Settings & Health ----------
class SettingsOut(BaseModel):
    app_name: str
    app_base_url: str
    smtp_configured: bool
    smtp_from_email: Optional[str] = None
    providers_available: List[str]

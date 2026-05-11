"""Generic customs/import data integration."""

from __future__ import annotations

from typing import Any

from .http import JsonHttpClient
from ..models import CustomsRecord


class CustomsDataClient:
    def __init__(
        self,
        api_base: str,
        api_key: str | None = None,
        import_endpoint: str = "/import-records",
        http: JsonHttpClient | None = None,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.import_endpoint = import_endpoint if import_endpoint.startswith("/") else f"/{import_endpoint}"
        self.http = http or JsonHttpClient()

    def search_importers(self, *, product: str, country: str | None = None, limit: int = 20) -> list[CustomsRecord]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        data = self.http.request_json(
            "GET",
            f"{self.api_base}{self.import_endpoint}",
            headers=headers,
            query={"q": product, "product": product, "country": country, "limit": limit},
        )
        rows = data.get("records") or data.get("results") or data.get("data") or []
        return [self._to_record(row) for row in rows[:limit] if isinstance(row, dict)]

    def _to_record(self, row: dict[str, Any]) -> CustomsRecord:
        importer = row.get("importer_name") or row.get("buyer_name") or row.get("company_name") or row.get("consignee") or "Unknown Importer"
        product = row.get("product_description") or row.get("description") or row.get("product") or row.get("goods_description") or ""
        return CustomsRecord(
            importer_name=str(importer),
            product_description=str(product),
            country=row.get("country") or row.get("destination_country") or row.get("import_country"),
            exporter_name=row.get("exporter_name") or row.get("supplier_name") or row.get("shipper"),
            hs_code=row.get("hs_code") or row.get("hscode"),
            shipment_date=row.get("shipment_date") or row.get("date"),
            source="customs",
            metadata=row,
        )

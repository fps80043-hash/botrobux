from __future__ import annotations

from typing import Any
import httpx

from app.config import settings


class APIClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.api_base_url,
            timeout=20.0,
            headers={
                'X-API-SECRET': settings.api_secret,
                'Content-Type': 'application/json',
            },
        )

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            return response.text

    async def get_optional(self, path: str, params: dict[str, Any] | None = None) -> Any | None:
        try:
            return await self.get(path, params=params)
        except Exception:
            return None

    async def post(self, path: str, json_data: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
        response = await self._client.post(path, json=json_data, params=params)
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            return response.text

    async def post_optional(self, path: str, json_data: dict[str, Any], params: dict[str, Any] | None = None) -> Any | None:
        try:
            return await self.post(path, json_data, params=params)
        except Exception:
            return None

    async def close(self) -> None:
        await self._client.aclose()


api_client = APIClient()

from __future__ import annotations

import httpx
from typing import Any

from app.config import settings


class APIClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.api_base_url.rstrip("/"),
            timeout=20.0,
            headers={
                "X-Internal-Secret": settings.api_secret,
                "Content-Type": "application/json",
            },
        )

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def post(self, path: str, json_data: dict[str, Any]) -> Any:
        response = await self._client.post(path, json=json_data)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()


api_client = APIClient()

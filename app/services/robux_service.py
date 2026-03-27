from __future__ import annotations

from app.config import settings
from app.services.api_client import api_client


class RobuxService:
    def _identity_params(self, telegram_id: int) -> dict:
        payload = {"telegram_id": telegram_id}
        if settings.test_site_user_id is not None:
            payload["site_user_id"] = settings.test_site_user_id
        return payload

    async def link_account(self, telegram_id: int, code: str):
        payload = {
            "telegram_id": telegram_id,
            "code": code,
        }
        if settings.test_site_user_id is not None:
            payload["site_user_id"] = settings.test_site_user_id
        return await api_client.post("/api/telegram/link", payload)

    async def get_profile(self, telegram_id: int):
        return await api_client.get("/api/users/me", params=self._identity_params(telegram_id))

    async def get_packages(self):
        return await api_client.get("/api/robux/packages")

    async def get_stock(self):
        return await api_client.get("/api/robux/stock")

    async def create_order(self, telegram_id: int, package_id: int, nickname: str, email: str | None = None):
        payload = self._identity_params(telegram_id)
        payload.update({
            "package_id": package_id,
            "nickname": nickname,
        })
        if email:
            payload["email"] = email
        return await api_client.post("/api/orders/create", payload)

    async def get_orders(self, telegram_id: int):
        return await api_client.get("/api/orders/my", params=self._identity_params(telegram_id))


robux_service = RobuxService()

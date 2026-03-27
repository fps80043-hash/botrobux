from __future__ import annotations

from app.services.api_client import api_client


class RobuxService:
    async def link_account(self, telegram_id: int, code: str):
        return await api_client.post("/api/telegram/link", {
            "telegram_id": telegram_id,
            "code": code,
        })

    async def get_profile(self, telegram_id: int):
        return await api_client.get("/api/users/me", params={"telegram_id": telegram_id})

    async def get_packages(self):
        return await api_client.get("/api/robux/packages")

    async def get_stock(self):
        return await api_client.get("/api/robux/stock")

    async def create_order(self, telegram_id: int, package_id: int, nickname: str, email: str | None = None):
        payload = {
            "telegram_id": telegram_id,
            "package_id": package_id,
            "nickname": nickname,
        }
        if email:
            payload["email"] = email
        return await api_client.post("/api/orders/create", payload)

    async def get_orders(self, telegram_id: int):
        return await api_client.get("/api/orders/my", params={"telegram_id": telegram_id})


robux_service = RobuxService()

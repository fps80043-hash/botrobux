from __future__ import annotations

from typing import Any

from app.config import settings
from app.services.api_client import api_client
from app.utils.formatters import pick


class SiteAPI:
    def identity_params(self, telegram_id: int) -> dict[str, Any]:
        data: dict[str, Any] = {
            'telegram_id': telegram_id,
            'tg_id': telegram_id,
        }
        if settings.test_site_user_id is not None:
            uid = settings.test_site_user_id
            data.update({
                'site_user_id': uid,
                'user_id': uid,
                'uid': uid,
                'id': uid,
            })
        return data

    async def profile(self, telegram_id: int) -> dict[str, Any]:
        params = self.identity_params(telegram_id)
        fallback: dict[str, Any] = {}
        if settings.test_site_user_id is not None:
            fallback = {
                'id': settings.test_site_user_id,
                'username': 'Admin' if settings.test_site_user_id == 1 else f'User {settings.test_site_user_id}',
                'is_admin': settings.test_site_user_id == 1 or telegram_id in settings.admin_ids,
            }
        try:
            data = await api_client.get(settings.endpoint_profile, params=params)
        except Exception:
            data = {}
        user = data.get('user') if isinstance(data, dict) and isinstance(data.get('user'), dict) else data
        if isinstance(user, dict) and user:
            if 'id' not in user and settings.test_site_user_id is not None:
                user['id'] = settings.test_site_user_id
            if settings.test_site_user_id == 1:
                user['is_admin'] = bool(user.get('is_admin', True))
            return user
        balance_data = await self.balance(telegram_id)
        fallback['balance'] = balance_data.get('balance', 0)
        return fallback

    async def balance(self, telegram_id: int) -> dict[str, Any]:
        params = self.identity_params(telegram_id)
        try:
            data = await api_client.get(settings.endpoint_balance, params=params)
        except Exception:
            return {'balance': 0, 'currency': 'RUB'}
        if isinstance(data, dict):
            if 'balance' in data:
                return data
            for key in ('user', 'data'):
                nested = data.get(key)
                if isinstance(nested, dict) and 'balance' in nested:
                    return nested
            for key in ('amount', 'value'):
                if key in data:
                    return {'balance': data[key], 'currency': data.get('currency', 'RUB')}
        return {'balance': data, 'currency': 'RUB'}

    async def stock(self) -> dict[str, Any]:
        data = await api_client.get(settings.endpoint_stock)
        if isinstance(data, dict):
            return {
                'available_robux': pick(data.get('available_robux'), data.get('robux'), data.get('stock'), default=0),
                'available_packages': pick(data.get('available_packages'), data.get('packages_count'), default=0),
                'status': data.get('status', 'ok'),
                'raw': data,
            }
        return {'available_robux': 0, 'available_packages': 0, 'status': 'unknown', 'raw': data}

    async def orders(self, telegram_id: int, limit: int = 10) -> list[dict[str, Any]]:
        params = self.identity_params(telegram_id)
        params['limit'] = limit
        data = await api_client.get(settings.endpoint_orders, params=params)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ('items', 'orders', 'transactions', 'data'):
                if isinstance(data.get(key), list):
                    return data[key]
        return []

    async def packages(self) -> list[dict[str, Any]]:
        try:
            data = await api_client.get(settings.endpoint_packages)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for key in ('items', 'packages', 'data'):
                    if isinstance(data.get(key), list):
                        return data[key]
        except Exception:
            pass

        config = await api_client.get(settings.endpoint_shop_config)
        if not isinstance(config, dict):
            return []
        for key in ('packages', 'robux_packages', 'catalog'):
            if isinstance(config.get(key), list):
                return config[key]
        price_per_robux = config.get('price_per_robux') or config.get('robux_price') or config.get('price')
        if price_per_robux:
            return [
                {'id': 1, 'title': '400 Robux', 'robux_amount': 400, 'price': round(float(price_per_robux) * 400)},
                {'id': 2, 'title': '800 Robux', 'robux_amount': 800, 'price': round(float(price_per_robux) * 800)},
                {'id': 3, 'title': '1700 Robux', 'robux_amount': 1700, 'price': round(float(price_per_robux) * 1700)},
            ]
        return []

    async def create_order(self, telegram_id: int, package_id: int, nickname: str, email: str | None = None) -> dict[str, Any]:
        payload = self.identity_params(telegram_id)
        payload.update({'package_id': package_id, 'nickname': nickname})
        if email:
            payload['email'] = email
        return await api_client.post(settings.endpoint_create_order, payload)

    async def link_account(self, telegram_id: int, code: str) -> dict[str, Any]:
        payload = self.identity_params(telegram_id)
        payload['code'] = code
        return await api_client.post(settings.endpoint_link, payload)

    async def is_admin(self, telegram_id: int) -> bool:
        if telegram_id in settings.admin_ids:
            return True
        try:
            profile = await self.profile(telegram_id)
        except Exception:
            return False
        return bool(profile.get('is_admin'))

    async def admin_get_config(self) -> dict[str, Any]:
        return await api_client.get(settings.endpoint_admin_get_config)

    async def admin_set_price(self, price_per_robux: float) -> dict[str, Any]:
        return await api_client.post(settings.endpoint_admin_update_config, {'price_per_robux': price_per_robux})

    async def admin_get_stock(self) -> dict[str, Any]:
        return await api_client.get(settings.endpoint_admin_get_stock)

    async def admin_set_stock(self, amount: int) -> dict[str, Any]:
        return await api_client.post(settings.endpoint_admin_update_stock, {'available_robux': amount})

    async def admin_orders(self) -> list[dict[str, Any]]:
        data = await api_client.get(settings.endpoint_admin_orders, params={'limit': 10})
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ('items', 'orders', 'data'):
                if isinstance(data.get(key), list):
                    return data[key]
        return []

    async def admin_find_user(self, query: str) -> dict[str, Any]:
        return await api_client.get(settings.endpoint_admin_find_user, params={'q': query})

    async def admin_set_balance(self, user_id: int, balance: float) -> dict[str, Any]:
        return await api_client.post(settings.endpoint_admin_update_balance, {'user_id': user_id, 'balance': balance})


site_api = SiteAPI()

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

    async def _get_first_success(self, paths: list[str], params: dict[str, Any] | None = None) -> Any:
        last_exc: Exception | None = None
        for path in paths:
            if not path:
                continue
            try:
                return await api_client.get(path, params=params)
            except Exception as exc:
                last_exc = exc
                continue
        if last_exc:
            raise last_exc
        return {}

    async def profile(self, telegram_id: int) -> dict[str, Any]:
        params = self.identity_params(telegram_id)
        fallback: dict[str, Any] = {
            'id': settings.test_site_user_id or '',
            'username': 'Admin' if settings.test_site_user_id == 1 else '',
            'is_admin': settings.test_site_user_id == 1 or telegram_id in settings.admin_ids,
            'balance': 0,
        }
        data = await api_client.get_optional(settings.endpoint_profile, params=params)
        user = data.get('user') if isinstance(data, dict) and isinstance(data.get('user'), dict) else data
        if isinstance(user, dict) and user:
            merged = {**fallback, **user}
            if merged.get('balance') in (None, ''):
                merged['balance'] = 0
            return merged
        return fallback

    async def balance(self, telegram_id: int) -> dict[str, Any]:
        params = self.identity_params(telegram_id)
        candidates = [
            settings.endpoint_balance,
            '/api/balance',
            '/api/user/balance',
            '/api/profile/balance',
            '/api/auth/balance',
            '/balance',
        ]
        for path in candidates:
            if not path:
                continue
            data = await api_client.get_optional(path, params=params)
            if not data:
                continue
            if isinstance(data, dict):
                if 'balance' in data:
                    return {'balance': data.get('balance', 0), 'currency': data.get('currency', 'RUB')}
                for key in ('user', 'data'):
                    nested = data.get(key)
                    if isinstance(nested, dict) and 'balance' in nested:
                        return {'balance': nested.get('balance', 0), 'currency': nested.get('currency', 'RUB')}
                for key in ('amount', 'value'):
                    if key in data:
                        return {'balance': data[key], 'currency': data.get('currency', 'RUB')}
            else:
                return {'balance': data, 'currency': 'RUB'}

        profile = await self.profile(telegram_id)
        return {'balance': profile.get('balance', profile.get('bal', 0)) or 0, 'currency': 'RUB'}

    async def stock(self) -> dict[str, Any]:
        candidates = [
            settings.endpoint_stock,
            '/api/shop/stock',
            '/api/stock',
            '/shop/stock',
            '/stock',
        ]
        for path in candidates:
            if not path:
                continue
            data = await api_client.get_optional(path)
            if not data:
                continue
            if isinstance(data, dict):
                amount = pick(data.get('available_robux'), data.get('robux'), data.get('stock'), data.get('amount'), default=0)
                packages = pick(data.get('available_packages'), data.get('packages_count'), default=0)
                if not packages:
                    for key in ('packages', 'items', 'data'):
                        if isinstance(data.get(key), list):
                            packages = len(data[key])
                            break
                return {
                    'available_robux': amount,
                    'available_packages': packages,
                    'status': data.get('status', 'ok' if amount else 'out_of_stock'),
                    'raw': data,
                }

        config = await self.shop_config()
        amount = pick(
            config.get('available_robux'),
            config.get('robux_stock'),
            config.get('stock'),
            config.get('stock_total'),
            default=0,
        )
        packages = 0
        for key in ('packages', 'robux_packages', 'catalog', 'items'):
            if isinstance(config.get(key), list):
                packages = len(config[key])
                break
        return {
            'available_robux': amount,
            'available_packages': packages,
            'status': 'ok' if amount else 'out_of_stock',
            'raw': config,
        }

    async def shop_config(self) -> dict[str, Any]:
        candidates = [
            settings.endpoint_shop_config,
            '/api/shop_config',
            '/api/shop/config',
            '/api/config/shop',
            '/shop_config',
        ]
        for path in candidates:
            if not path:
                continue
            data = await api_client.get_optional(path)
            if isinstance(data, dict):
                return data
        return {}

    async def orders(self, telegram_id: int, limit: int = 10) -> list[dict[str, Any]]:
        params = self.identity_params(telegram_id)
        params['limit'] = limit
        candidates = [
            settings.endpoint_orders,
            '/api/tx',
            '/api/orders/my',
            '/tx',
        ]
        for path in candidates:
            if not path:
                continue
            data = await api_client.get_optional(path, params=params)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for key in ('items', 'orders', 'transactions', 'data'):
                    if isinstance(data.get(key), list):
                        return data[key]
        return []

    async def packages(self) -> list[dict[str, Any]]:
        for path in [settings.endpoint_packages, '/api/shop/packages', '/api/packages']:
            if not path:
                continue
            data = await api_client.get_optional(path)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for key in ('items', 'packages', 'data'):
                    if isinstance(data.get(key), list):
                        return data[key]

        config = await self.shop_config()
        for key in ('packages', 'robux_packages', 'catalog'):
            if isinstance(config.get(key), list):
                return config[key]
        price_per_robux = config.get('price_per_robux') or config.get('robux_price') or config.get('price')
        if price_per_robux:
            try:
                price_per_robux = float(price_per_robux)
            except Exception:
                price_per_robux = None
        if price_per_robux:
            return [
                {'id': 1, 'title': '400 Robux', 'robux_amount': 400, 'price': round(price_per_robux * 400)},
                {'id': 2, 'title': '800 Robux', 'robux_amount': 800, 'price': round(price_per_robux * 800)},
                {'id': 3, 'title': '1700 Robux', 'robux_amount': 1700, 'price': round(price_per_robux * 1700)},
            ]
        return []

    async def create_order(self, telegram_id: int, package_id: int, nickname: str, email: str | None = None) -> dict[str, Any]:
        payload = self.identity_params(telegram_id)
        payload.update({'package_id': package_id, 'nickname': nickname})
        if email:
            payload['email'] = email
        result = await api_client.post_optional(settings.endpoint_create_order, payload)
        return result or {'status': 'error'}

    async def link_account(self, telegram_id: int, code: str) -> dict[str, Any]:
        payload = self.identity_params(telegram_id)
        payload['code'] = code
        result = await api_client.post_optional(settings.endpoint_link, payload)
        return result or {'message': 'Не удалось привязать аккаунт'}

    async def is_admin(self, telegram_id: int) -> bool:
        if telegram_id in settings.admin_ids:
            return True
        profile = await self.profile(telegram_id)
        return bool(profile.get('is_admin'))

    async def admin_get_config(self) -> dict[str, Any]:
        result = await api_client.get_optional(settings.endpoint_admin_get_config)
        return result or {}

    async def admin_set_price(self, price_per_robux: float) -> dict[str, Any]:
        result = await api_client.post_optional(settings.endpoint_admin_update_config, {'price_per_robux': price_per_robux})
        return result or {'ok': False}

    async def admin_get_stock(self) -> dict[str, Any]:
        result = await api_client.get_optional(settings.endpoint_admin_get_stock)
        return result or {}

    async def admin_set_stock(self, amount: int) -> dict[str, Any]:
        result = await api_client.post_optional(settings.endpoint_admin_update_stock, {'available_robux': amount})
        return result or {'ok': False}

    async def admin_orders(self) -> list[dict[str, Any]]:
        data = await api_client.get_optional(settings.endpoint_admin_orders, params={'limit': 10})
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ('items', 'orders', 'data'):
                if isinstance(data.get(key), list):
                    return data[key]
        return []

    async def admin_find_user(self, query: str) -> dict[str, Any]:
        result = await api_client.get_optional(settings.endpoint_admin_find_user, params={'q': query})
        return result or {}

    async def admin_set_balance(self, user_id: int, balance: float) -> dict[str, Any]:
        result = await api_client.post_optional(settings.endpoint_admin_update_balance, {'user_id': user_id, 'balance': balance})
        return result or {'ok': False}


site_api = SiteAPI()

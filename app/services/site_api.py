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

    async def health(self) -> dict[str, Any]:
        return await api_client.get_optional(settings.endpoint_health) or {}

    async def profile(self, telegram_id: int) -> dict[str, Any]:
        params = self.identity_params(telegram_id)
        fallback: dict[str, Any] = {
            'id': settings.test_site_user_id or '',
            'username': 'Admin' if settings.test_site_user_id == 1 else '',
            'is_admin': settings.test_site_user_id == 1 or telegram_id in settings.admin_ids,
            'balance': 0,
            'premium': False,
        }
        data = await api_client.get_optional(settings.endpoint_profile, params=params)
        user = data.get('user') if isinstance(data, dict) and isinstance(data.get('user'), dict) else data
        if isinstance(user, dict) and user:
            merged = {**fallback, **user}
            merged['balance'] = int(merged.get('balance') or 0)
            return merged
        return fallback

    async def balance(self, telegram_id: int) -> dict[str, Any]:
        params = self.identity_params(telegram_id)
        data = await api_client.get_optional(settings.endpoint_balance, params=params)
        if isinstance(data, dict) and 'balance' in data:
            return {'balance': int(data.get('balance') or 0), 'currency': data.get('currency', 'RUB')}
        profile = await self.profile(telegram_id)
        return {'balance': int(profile.get('balance') or 0), 'currency': 'RUB'}

    async def stock(self) -> dict[str, Any]:
        data = await api_client.get_optional(settings.endpoint_stock)
        if isinstance(data, dict):
            amount = pick(data.get('available_robux'), data.get('available'), data.get('robux'), data.get('stock'), default=0)
            packages = pick(data.get('available_packages'), data.get('accounts'), default=0)
            return {
                'available_robux': int(amount or 0),
                'available_packages': int(packages or 0),
                'status': data.get('status', 'ok' if int(amount or 0) > 0 else 'out_of_stock'),
                'raw': data,
            }
        return {'available_robux': 0, 'available_packages': 0, 'status': 'out_of_stock', 'raw': {}}

    async def orders(self, telegram_id: int, limit: int = 10) -> list[dict[str, Any]]:
        params = self.identity_params(telegram_id)
        params['limit'] = limit
        data = await api_client.get_optional(settings.endpoint_orders, params=params)
        if isinstance(data, dict) and isinstance(data.get('items'), list):
            return data['items']
        if isinstance(data, list):
            return data
        return []

    async def packages(self) -> list[dict[str, Any]]:
        catalog = await api_client.get_optional(settings.endpoint_shop_catalog)
        if isinstance(catalog, dict) and isinstance(catalog.get('items'), list) and catalog.get('items'):
            items = []
            for item in catalog['items']:
                if not isinstance(item, dict):
                    continue
                price = item.get('price') or item.get('price_rub') or 0
                items.append({
                    'id': item.get('id') or item.get('raw', {}).get('id') or item.get('title') or len(items)+1,
                    'title': item.get('title') or item.get('name') or 'Товар',
                    'price': price,
                    'robux_amount': item.get('robux_amount') or item.get('amount') or 0,
                    'raw': item,
                })
            if items:
                return items[:12]

        presets = [100, 200, 400, 800, 1700]
        items: list[dict[str, Any]] = []
        for idx, amount in enumerate(presets, start=1):
            quote = await api_client.get_optional(settings.endpoint_quote, params={'amount': amount})
            if isinstance(quote, dict):
                price = pick(quote.get('price'), quote.get('rub_price'), quote.get('rub_total'), quote.get('amount_rub'), default=0)
                items.append({'id': idx, 'title': f'{amount} Robux', 'robux_amount': amount, 'price': price})
        return items

    async def create_order(self, telegram_id: int, package_id: int, nickname: str, email: str | None = None) -> dict[str, Any]:
        packages = await self.packages()
        package = next((x for x in packages if str(x.get('id')) == str(package_id)), None)
        if not package:
            return {'status': 'error', 'message': 'Пакет не найден'}
        payload = {
            'robux_amount': int(package.get('robux_amount') or 0),
            'nickname': nickname,
            'email': email or '',
        }
        # Keep compatibility with your existing web endpoint.
        result = await api_client.post_optional(settings.endpoint_create_order, payload, params=self.identity_params(telegram_id))
        return result or {'status': 'error', 'message': 'Не удалось оформить заказ'}

    async def link_account(self, telegram_id: int, code: str) -> dict[str, Any]:
        # test mode: allow sending plain user id like "1"
        site_user_id = 0
        if code.isdigit():
            site_user_id = int(code)
        elif settings.test_site_user_id:
            site_user_id = settings.test_site_user_id
        payload = {
            'site_user_id': site_user_id,
            'telegram_id': telegram_id,
            'telegram_username': '',
            'code': code,
        }
        result = await api_client.post_optional(settings.endpoint_link, payload)
        return result or {'message': 'Не удалось привязать аккаунт'}

    async def is_admin(self, telegram_id: int) -> bool:
        if telegram_id in settings.admin_ids:
            return True
        profile = await self.profile(telegram_id)
        return bool(profile.get('is_admin'))

    async def admin_get_config(self, telegram_id: int) -> dict[str, Any]:
        params = self.identity_params(telegram_id)
        result = await api_client.get_optional(settings.endpoint_admin_get_config, params=params)
        return result or {}

    async def admin_set_price(self, telegram_id: int, price_per_robux: float) -> dict[str, Any]:
        params = self.identity_params(telegram_id)
        result = await api_client.post_optional(settings.endpoint_admin_update_config, {'rub_per_robux': price_per_robux}, params=params)
        return result or {'ok': False}

    async def admin_get_stock(self, telegram_id: int) -> dict[str, Any]:
        result = await self.admin_get_config(telegram_id)
        return result.get('stock') if isinstance(result, dict) and isinstance(result.get('stock'), dict) else result

    async def admin_set_stock(self, telegram_id: int, amount: int) -> dict[str, Any]:
        params = self.identity_params(telegram_id)
        result = await api_client.post_optional(settings.endpoint_admin_update_config, {'stock_sell': amount, 'stock_show': amount}, params=params)
        return result or {'ok': False}

    async def admin_orders(self, telegram_id: int, limit: int = 10) -> list[dict[str, Any]]:
        params = self.identity_params(telegram_id)
        params['limit'] = limit
        result = await api_client.get_optional(settings.endpoint_admin_orders, params=params)
        if isinstance(result, dict) and isinstance(result.get('items'), list):
            return result['items']
        if isinstance(result, list):
            return result
        return []

    async def admin_find_user(self, telegram_id: int, query: str) -> dict[str, Any]:
        params = self.identity_params(telegram_id)
        params['q'] = query
        result = await api_client.get_optional(settings.endpoint_admin_find_user, params=params)
        if isinstance(result, dict) and isinstance(result.get('items'), list) and result['items']:
            return {'user': result['items'][0], 'items': result['items']}
        return result or {}

    async def admin_set_balance(self, telegram_id: int, user_id: int, new_balance: float) -> dict[str, Any]:
        params = self.identity_params(telegram_id)
        # endpoint adjusts by delta, so resolve current balance first
        user_info = await self.admin_find_user(telegram_id, str(user_id))
        user = user_info.get('user') if isinstance(user_info, dict) else None
        current = float((user or {}).get('balance') or 0)
        delta = int(round(float(new_balance) - current))
        result = await api_client.post_optional(settings.endpoint_admin_update_balance, {'user_id': user_id, 'delta': delta, 'reason': 'telegram bot admin'}, params=params)
        return result or {'ok': False}


site_api = SiteAPI()

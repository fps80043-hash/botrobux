from __future__ import annotations

from dataclasses import dataclass, field
import os
from dotenv import load_dotenv

load_dotenv()


def _optional_int(name: str) -> int | None:
    raw = os.getenv(name, '').strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _int_set(name: str) -> set[int]:
    raw = os.getenv(name, '').strip()
    if not raw:
        return set()
    result: set[int] = set()
    for part in raw.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            result.add(int(part))
        except ValueError:
            continue
    return result


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv('BOT_TOKEN', '')
    api_base_url: str = os.getenv('API_BASE_URL', '').rstrip('/')
    api_secret: str = os.getenv('API_SECRET', '')
    test_site_user_id: int | None = _optional_int('TEST_SITE_USER_ID')
    admin_ids: set[int] = field(default_factory=lambda: _int_set('ADMIN_IDS'))
    default_start_gif: str = os.getenv('DEFAULT_START_GIF', '').strip()
    terms_version: str = os.getenv('TERMS_VERSION', '1').strip() or '1'

    endpoint_profile: str = os.getenv('ENDPOINT_PROFILE', '/api/auth/me')
    endpoint_balance: str = os.getenv('ENDPOINT_BALANCE', '/balance')
    endpoint_stock: str = os.getenv('ENDPOINT_STOCK', '/stock')
    endpoint_orders: str = os.getenv('ENDPOINT_ORDERS', '/tx')
    endpoint_packages: str = os.getenv('ENDPOINT_PACKAGES', '/api/robux/packages')
    endpoint_shop_config: str = os.getenv('ENDPOINT_SHOP_CONFIG', '/shop_config')
    endpoint_create_order: str = os.getenv('ENDPOINT_CREATE_ORDER', '/api/orders/create')
    endpoint_link: str = os.getenv('ENDPOINT_LINK', '/api/telegram/link')

    endpoint_admin_get_config: str = os.getenv('ENDPOINT_ADMIN_GET_CONFIG', '/api/admin/shop/config')
    endpoint_admin_update_config: str = os.getenv('ENDPOINT_ADMIN_UPDATE_CONFIG', '/api/admin/shop/config')
    endpoint_admin_get_stock: str = os.getenv('ENDPOINT_ADMIN_GET_STOCK', '/api/admin/stock')
    endpoint_admin_update_stock: str = os.getenv('ENDPOINT_ADMIN_UPDATE_STOCK', '/api/admin/stock')
    endpoint_admin_orders: str = os.getenv('ENDPOINT_ADMIN_ORDERS', '/api/admin/orders')
    endpoint_admin_find_user: str = os.getenv('ENDPOINT_ADMIN_FIND_USER', '/api/admin/users/find')
    endpoint_admin_update_balance: str = os.getenv('ENDPOINT_ADMIN_UPDATE_BALANCE', '/api/admin/users/balance')


settings = Settings()

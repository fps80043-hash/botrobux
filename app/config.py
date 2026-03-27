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
    build_tag: str = os.getenv('BUILD_TAG', 'bot-api-v1')
    bot_token: str = os.getenv('BOT_TOKEN', '')
    api_base_url: str = os.getenv('API_BASE_URL', '').rstrip('/')
    api_secret: str = os.getenv('API_SECRET', '')
    test_site_user_id: int | None = _optional_int('TEST_SITE_USER_ID')
    admin_ids: set[int] = field(default_factory=lambda: _int_set('ADMIN_IDS'))
    default_start_gif: str = os.getenv('DEFAULT_START_GIF', '').strip()
    terms_version: str = os.getenv('TERMS_VERSION', '1').strip() or '1'

    endpoint_health: str = os.getenv('ENDPOINT_HEALTH', '/api/bot/health').strip() or '/api/bot/health'
    endpoint_profile: str = os.getenv('ENDPOINT_PROFILE', '/api/bot/profile').strip() or '/api/bot/profile'
    endpoint_balance: str = os.getenv('ENDPOINT_BALANCE', '/api/bot/balance').strip() or '/api/bot/balance'
    endpoint_stock: str = os.getenv('ENDPOINT_STOCK', '/api/bot/robux/stock').strip() or '/api/bot/robux/stock'
    endpoint_quote: str = os.getenv('ENDPOINT_QUOTE', '/api/bot/robux/quote').strip() or '/api/bot/robux/quote'
    endpoint_orders: str = os.getenv('ENDPOINT_ORDERS', '/api/bot/robux/orders').strip() or '/api/bot/robux/orders'
    endpoint_shop_catalog: str = os.getenv('ENDPOINT_SHOP_CATALOG', '/api/bot/shop/catalog').strip() or '/api/bot/shop/catalog'
    endpoint_shop_orders: str = os.getenv('ENDPOINT_SHOP_ORDERS', '/api/bot/shop/orders').strip() or '/api/bot/shop/orders'
    endpoint_link: str = os.getenv('ENDPOINT_LINK', '/api/bot/telegram/link').strip() or '/api/bot/telegram/link'
    endpoint_create_order: str = os.getenv('ENDPOINT_CREATE_ORDER', '/api/robux/order_create').strip() or '/api/robux/order_create'

    endpoint_admin_get_config: str = os.getenv('ENDPOINT_ADMIN_GET_CONFIG', '/api/bot/admin/robux/settings').strip() or '/api/bot/admin/robux/settings'
    endpoint_admin_update_config: str = os.getenv('ENDPOINT_ADMIN_UPDATE_CONFIG', '/api/bot/admin/robux/settings').strip() or '/api/bot/admin/robux/settings'
    endpoint_admin_orders: str = os.getenv('ENDPOINT_ADMIN_ORDERS', '/api/bot/admin/orders/recent').strip() or '/api/bot/admin/orders/recent'
    endpoint_admin_find_user: str = os.getenv('ENDPOINT_ADMIN_FIND_USER', '/api/bot/admin/users/find').strip() or '/api/bot/admin/users/find'
    endpoint_admin_update_balance: str = os.getenv('ENDPOINT_ADMIN_UPDATE_BALANCE', '/api/bot/admin/balance_adjust').strip() or '/api/bot/admin/balance_adjust'


settings = Settings()

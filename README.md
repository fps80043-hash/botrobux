# RBX-ST Telegram Bot (Bot API edition)

This build is wired to the new `/api/bot/*` endpoints.

## Railway
Start command:

```bash
python -m app.main
```

Variables:

```env
BOT_TOKEN=...
API_BASE_URL=https://your-domain
API_SECRET=the_same_BOT_API_SECRET_from_site
TEST_SITE_USER_ID=1
ADMIN_IDS=1
DEFAULT_START_GIF=
BUILD_TAG=bot-api-v1
```

## Main endpoints used
- `/api/bot/profile`
- `/api/bot/balance`
- `/api/bot/robux/stock`
- `/api/bot/robux/quote`
- `/api/bot/robux/orders`
- `/api/bot/telegram/link`
- `/api/bot/admin/robux/settings`
- `/api/bot/admin/users/find`
- `/api/bot/admin/balance_adjust`
- `/api/bot/admin/orders/recent`

## Notes
- Profile/balance/admin are now read through the bot API, not browser cookies.
- Test mode with `TEST_SITE_USER_ID=1` is supported.
- Price/stock changes from Telegram sync with the site through the shared backend.

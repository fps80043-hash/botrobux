# RBX Store — Telegram Bot

Бот для пользователей сайта **RBX ST Shop**: продажа Robux, проверка баланса, отслеживание заказов, привязка профиля Telegram ↔ сайт.

## Что умеет

**Для пользователей:**
- 💎 Покупка Robux — стоковые пресеты + произвольная сумма, расчёт цены и проверка баланса
- 👤 Профиль — баланс, ID, email, статус Premium, привязка Telegram-аккаунта
- 🛒 Каталог магазина — навигация по категориям, цены, описания (read-only — оплата на сайте)
- 📦 Заказы — последние заказы Robux + покупки магазина с актуальным статусом
- 🔗 Привязка аккаунта по 6-значному коду (генерируется на сайте)

**Для админов:**
- 📊 Последние Robux-заказы со статусами
- 🔍 Поиск пользователя по нику / email / ID
- 💎 Текущие настройки Robux (наличие, курс)

## Архитектура

```
┌─────────────────┐       HTTPS + X-API-SECRET         ┌──────────────────┐
│   Telegram      │ ◄────────────────────────────────► │  rbx-site        │
│   (this bot)    │   /api/bot/profile, /balance,      │  FastAPI backend │
│   aiogram 3     │   /robux/stock, /orders, etc.      │  (main.py)       │
└─────────────────┘                                    └──────────────────┘
        ▲                                                       ▲
        │                                                       │
        │ /link <code>                                          │ User logs in
        │                                                       │ → Profile → Telegram-bot
        │                                                       │ → "Получить код"
        └───────── 6-digit code (10 min TTL) ───────────────────┘
```

Бот никогда не получает прямой доступ к БД сайта — все взаимодействия через `/api/bot/*` endpoints на бэкенде. Аутентификация: общий секрет в HTTP-header `X-API-SECRET` + идентификация пользователя по `telegram_id` (через таблицу `telegram_links`).

## Установка

### 1. Создай бота

Открой [@BotFather](https://t.me/BotFather) → `/newbot` → задай имя и username → скопируй токен.

### 2. Настрой переменные

```bash
cd bot
cp .env.example .env
nano .env
```

Заполни:
- `BOT_TOKEN` — от BotFather
- `SITE_URL` — публичный URL твоего сайта (например `https://rbx-store-production.up.railway.app`)
- `SITE_API_SECRET` — должен **совпадать** со значением переменной `BOT_API_SECRET` на сайте (см. Railway → Variables)
- `ADMIN_TG_IDS` — необязательно, через запятую: твой Telegram ID и других админов (узнать ID — `@userinfobot`)

### 3. Запуск локально

```bash
pip install -r requirements.txt
python bot.py
```

Если всё ок — увидишь в логах:
```
INFO  | bot      | Bot started as @your_bot (id=..., RBX Store Bot)
INFO  | bot      | Site reachable, build=...
```

### 4. Деплой

#### Railway (рекомендуется)

1. Залогинься в Railway
2. New project → Deploy from GitHub (или загрузи папку `bot/` отдельным репо)
3. Добавь те же переменные что в `.env`
4. Railway автоматически подхватит `Dockerfile`

#### Docker

```bash
docker build -t rbx-bot .
docker run --env-file .env rbx-bot
```

#### systemd (на VPS)

Скопируй проект в `/opt/rbx-bot`, создай сервис `/etc/systemd/system/rbx-bot.service`:

```ini
[Unit]
Description=RBX Store Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/rbx-bot
EnvironmentFile=/opt/rbx-bot/.env
ExecStart=/opt/rbx-bot/.venv/bin/python bot.py
Restart=on-failure
RestartSec=5
User=rbx-bot

[Install]
WantedBy=multi-user.target
```

Затем `sudo systemctl enable --now rbx-bot`.

## Как пользователь привязывает аккаунт

1. Открыть сайт, залогиниться
2. Профиль → вкладка **Безопасность**
3. В блоке «Telegram-бот» нажать **«Получить код привязки»**
4. Скопировать показанный 6-значный код
5. В Telegram открыть бота, отправить `/link 123456` (где 123456 — код)
6. Готово — бот покажет «✅ Аккаунт привязан»

Код действителен 10 минут. Один TG-аккаунт может быть привязан только к одному сайт-аккаунту в любой момент времени (привязка к новому автоматически разрывает старую).

## Безопасность

- **Бот никогда не запрашивает пароль или email** — привязка только по одноразовому коду
- Все запросы между ботом и сайтом авторизуются общим секретом в header — бот не может представляться сайтом наоборот
- Покупка Robux **не происходит внутри бота** — пользователь оформляет заказ на сайте (там есть полная UX с проверкой геймпасса, резервированием, captcha и т.д.). Бот только показывает котировку и отправляет на сайт.
- Админ-команды доступны только если: (а) Telegram ID есть в `ADMIN_TG_IDS`, **или** (б) привязанный сайт-аккаунт имеет `is_admin=1`

## Структура проекта

```
bot/
├── bot.py              # main entry point
├── config.py           # env loading + constants
├── api.py              # async HTTP client to /api/bot/*
├── utils.py            # formatting helpers (esc, fmt_rub, fmt_relative, ...)
├── keyboards.py        # all inline keyboards
├── handlers/
│   ├── __init__.py
│   ├── start.py        # /start, /menu, /help
│   ├── link.py         # /link, /unlink, deep-link binding
│   ├── profile.py      # /profile, /balance
│   ├── robux.py        # /buy, /robux + FSM for custom amount
│   ├── orders.py       # /orders + tabs (Robux / Shop)
│   ├── shop.py         # /shop catalog browsing
│   └── admin.py        # /admin + admin actions (FSM for user search)
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## Логи

Бот пишет в stdout. Уровень регулируется переменной `LOG_LEVEL` (`DEBUG`/`INFO`/`WARNING`/`ERROR`).

## Команды

| Команда            | Описание                              |
|--------------------|---------------------------------------|
| `/start`           | Главное меню                          |
| `/menu`            | Главное меню                          |
| `/profile`         | Профиль и баланс                      |
| `/balance`         | Быстрая проверка баланса              |
| `/buy` или `/robux`| Покупка Robux                         |
| `/orders`          | Свои заказы (Robux + магазин)         |
| `/shop`            | Каталог магазина                      |
| `/link <код>`      | Привязка аккаунта сайта               |
| `/unlink`          | Отвязка                               |
| `/admin`           | Админ-панель (только админам)         |
| `/help`            | Справка по командам                   |

## Troubleshooting

**Бот запустился, но команды не работают, в логах `403 Forbidden`:**
- `SITE_API_SECRET` в `.env` не совпадает с `BOT_API_SECRET` на сайте → совпасти их

**Команды не отображаются в списке:**
- Telegram кэширует список команд ~1 минуту, перезайди в чат с ботом

**`/link 123456` выдаёт «Код не принят»:**
- Код одноразовый и живёт 10 минут — сгенерируй новый на сайте
- Цифры могут быть с пробелами/тире — бот их вычистит, но проверь что прислал именно сайт-код, а не TG-ID или что-то ещё

**Изменения в коде не применяются:**
- Перезапусти процесс бота (он не hot-reload). На Railway/Docker — рестарт сервиса.

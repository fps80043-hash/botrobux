# Контракт API для синхронизации сайта и Telegram-бота

## Общий принцип
Сайт остается источником истины. Telegram-бот только вызывает backend.

## Обязательные сущности
- users
- wallets / balances
- robux_stock
- robux_packages
- orders
- telegram_links

## Минимальная таблица для привязки Telegram
```sql
create table telegram_links (
    id bigserial primary key,
    user_id bigint not null,
    telegram_id bigint not null unique,
    linked_at timestamp not null default now()
);
```

## Минимальная таблица кодов привязки
```sql
create table telegram_link_codes (
    id bigserial primary key,
    user_id bigint not null,
    code varchar(32) not null unique,
    is_used boolean not null default false,
    expires_at timestamp not null,
    created_at timestamp not null default now()
);
```

## Логика заказа должна жить в одном месте
На backend должен быть единый сервис типа:

```python
class RobuxOrderService:
    def create_order(self, user_id: int, package_id: int, nickname: str, email: str | None):
        # 1. берем пакет
        # 2. проверяем баланс
        # 3. проверяем остаток robux
        # 4. создаем заказ
        # 5. списываем баланс
        # 6. уменьшаем остаток
        # 7. коммитим транзакцию
        pass
```

И сайт, и Telegram должны вызывать именно этот сервис.

## Важные проверки
- все списания только в транзакции
- нельзя дать оформить заказ при нехватке остатка
- нельзя дать уйти в минус по балансу
- идемпотентность на создание заказа полезна
- логирование всех операций обязательно

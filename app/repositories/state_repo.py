from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path('bot_state.db')


class StateRepo:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self.conn.execute(
            '''
            create table if not exists accepted_terms (
                telegram_id integer not null,
                version text not null,
                accepted_at text default current_timestamp,
                primary key (telegram_id, version)
            )
            '''
        )
        self.conn.execute(
            '''
            create table if not exists bot_settings (
                key text primary key,
                value text not null
            )
            '''
        )
        self.conn.commit()

    def has_accepted_terms(self, telegram_id: int, version: str) -> bool:
        row = self.conn.execute(
            'select 1 from accepted_terms where telegram_id = ? and version = ?',
            (telegram_id, version),
        ).fetchone()
        return bool(row)

    def accept_terms(self, telegram_id: int, version: str) -> None:
        self.conn.execute(
            'insert or ignore into accepted_terms (telegram_id, version) values (?, ?)',
            (telegram_id, version),
        )
        self.conn.commit()

    def get_setting(self, key: str) -> str | None:
        row = self.conn.execute('select value from bot_settings where key = ?', (key,)).fetchone()
        return row['value'] if row else None

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            'insert into bot_settings (key, value) values (?, ?) on conflict(key) do update set value = excluded.value',
            (key, value),
        )
        self.conn.commit()


state_repo = StateRepo()

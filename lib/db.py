import sqlite3
from typing import Union

conn = sqlite3.connect("items.db")
cursor = conn.cursor()


def insert(table: str, column_values: dict):
    columns = ', '.join(column_values.keys())
    values = [tuple(column_values.values())]
    placeholders = ", ".join("?" * len(column_values.keys()))
    cursor.executemany(
        f"INSERT INTO {table} "
        f"({columns}) "
        f"VALUES ({placeholders})",
        values)
    conn.commit()


def get_item_name_id(hash_name: str, table: str) -> Union[int, None]:
    cursor.execute(f'SELECT item_nameid FROM {table} WHERE hash_name="{hash_name}"')
    item_nameid = cursor.fetchone()
    if not item_nameid:
        return None

    return int(*item_nameid)


def get_game_name_with_item_name(hash_name: str) -> Union[str, None]:
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table'")
    table_names = cursor.fetchall()
    for table_name in table_names:
        cursor.execute(f'SELECT COUNT(*) FROM {str(*table_name)} WHERE hash_name="{hash_name}"')
        if bool(*cursor.fetchone()):
            return str(*table_name)
    return None


def get_cursor():
    return cursor


def _init_db():
    """Инициализирует БД"""
    with open("createdb.sql", "r") as f:
        sql = f.read()
    cursor.executescript(sql)
    conn.commit()


def check_db_exists():
    """Проверяет, инициализирована ли БД, если нет — инициализирует"""
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table'")
    table_exists = cursor.fetchall()
    if table_exists:
        return
    _init_db()


class NoHashName(Exception):
    pass


check_db_exists()

import pytest
from models import database
from models.database import get_db_connection, get_db, init_db, get_db_stats
import sqlite3

def test_get_db_connection(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    conn = get_db_connection()
    try:
        assert conn is not None
        assert conn.row_factory == sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        assert cursor.fetchone()[0] == 1
    finally:
        conn.close()


def test_get_db_commit(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT)")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO test_table (value) VALUES (?)", ("test",))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM test_table WHERE value = 'test'")
        result = cursor.fetchone()
        assert result[0] == "test"


def test_get_db_rollback(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT)")
    with pytest.raises(RuntimeError):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO test_table (value) VALUES (?)", ("should be rolled back",))
            raise RuntimeError("test exception")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM test_table WHERE value = 'should be rolled back'")
        result = cursor.fetchone()
        assert result is None    


def test_init_db_valid(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE judgments (id INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT)")
    stats = init_db()
    assert stats['status'] == 'ok'
    assert stats['total_judgments'] == 0


def test_init_db_invalid(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    with pytest.raises(RuntimeError):
        init_db()

def test_get_db_stats_valid(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE judgments (id INTEGER PRIMARY KEY AUTOINCREMENT, compensation INTEGER)")
        cursor.execute("INSERT INTO judgments (compensation) VALUES (?)", (100000,))
        cursor.execute("INSERT INTO judgments (compensation) VALUES (?)", (200000,))
        cursor.execute("INSERT INTO judgments (compensation) VALUES (?)", (300000,))
        cursor.execute("INSERT INTO judgments (compensation) VALUES (?)", (0,))
    stats = get_db_stats()  
    assert stats['total_judgments'] == 4
    assert stats['total_compensations'] == 3
    assert stats['avg_compensation'] == 200000
    assert stats['db_size_mb'] > 0
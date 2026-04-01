import sqlite3
from models import database
from models.database import get_db
import json
import numpy as np
from api import health
from services import clear_vector_cache

def test_health_check(client, tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE judgments (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, case_number TEXT, court TEXT, date TEXT, compensation INTEGER, facts TEXT, reasoning TEXT, decision TEXT, full_text TEXT, evidence_types TEXT, vector BLOB)")
        cursor.execute("INSERT INTO judgments (title, case_number, court, date, compensation, facts, reasoning, decision, full_text, evidence_types, vector) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("案由", "112年度訴字第972號", "臺灣新北地方法院", "20210615", 200000, "事實", "理由", "主文", "判決全文", json.dumps(["定位截圖","錄影畫面","現場照片"]), np.random.rand(1536).astype(np.float32).tobytes()))
    
    clear_vector_cache()
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['database'] is not None
    assert data['vector_cache_status'] == "loaded"
    assert data['vector_cache_count'] > 0
    assert data['redis'] in ["ok", "down"]
    assert data['version'] == '1.0.0'
    assert data['timestamp'] is not None


def test_health_check_db_error(client, monkeypatch):
    def mock_get_db_stats_fail():
        raise Exception("Database connection refused")
    monkeypatch.setattr(health, "get_db_stats", mock_get_db_stats_fail)
    response = client.get('/api/health')
    assert response.status_code == 503
    data = response.get_json()
    assert data['status'] == "error"
    assert "Database connection refused" in data['error']


def test_health_check_vector_cache_error(client, monkeypatch):
    def mock_get_db_stats():
        return {
            'total_judgments': 10000,
            'total_compensations': 1000,
            'avg_compensation': 100000,
            'db_size_mb': 100
        }
    def mock_vector_cache_fail():
        raise Exception("Vector cache error")
    monkeypatch.setattr(health, "get_db_stats", mock_get_db_stats)
    monkeypatch.setattr(health, "get_vector_cache", mock_vector_cache_fail)
    response = client.get('/api/health')
    assert response.status_code == 503
    data = response.get_json()
    assert data['status'] == "error"
    assert  "Vector cache error" in data['error']


def test_health_check_redis_error(client, monkeypatch):
    def mock_get_db_stats():
        return {
            'total_judgments': 10000,
            'total_compensations': 1000,
            'avg_compensation': 100000,
            'db_size_mb': 100
        }
    def mock_get_vector_cache():
        return [1, 2, 3], np.array([[1, 2, 3]])
    def mock_get_redis_client_fail():
        return None
    monkeypatch.setattr(health, "get_db_stats", mock_get_db_stats)
    monkeypatch.setattr(health, "get_vector_cache", mock_get_vector_cache)
    monkeypatch.setattr(health, "get_redis_client", mock_get_redis_client_fail)
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "ok"
    assert data['redis'] == "down"
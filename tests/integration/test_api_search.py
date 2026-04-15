import sqlite3
from models import database
from models.database import get_db
import json
import numpy as np
from services import search_service, vector_service
import pytest
from api import search


@pytest.fixture
def mock_db_with_data(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE judgments (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, case_number TEXT, court TEXT, date TEXT, compensation INTEGER, facts TEXT, reasoning TEXT, decision TEXT, full_text TEXT, evidence_types TEXT, vector BLOB)"
        )
        cursor.execute(
            "INSERT INTO judgments (title, case_number, court, date, compensation, facts, reasoning, decision, full_text, evidence_types, vector) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "案由",
                "112年度訴字第972號",
                "臺灣新北地方法院",
                "20210615",
                200000,
                "事實",
                "理由",
                "主文",
                "判決全文",
                json.dumps(["定位截圖", "錄影畫面", "現場照片"]),
                np.random.rand(1536).astype(np.float32).tobytes(),
            ),
        )
    return test_db_path


def test_search(client, mock_db_with_data, monkeypatch):
    monkeypatch.setattr(
        search_service,
        "query_embeddings",
        lambda x: np.random.rand(1536).astype(np.float32),
    )
    vector_service.clear_vector_cache()
    response = client.post(
        "/api/search",
        json={
            "query": "配偶與第三人外遇交往長達五年以上，期間多次單獨出國同遊，有出入境紀錄與社群軟體的打卡照片為證。",
            "top_k": 10,
            "min_similarity": 0.0,
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
    assert "stats" in data
    assert (
        data["query"]
        == "配偶與第三人外遇交往長達五年以上，期間多次單獨出國同遊，有出入境紀錄與社群軟體的打卡照片為證。"
    )
    assert "search_time_ms" in data


def test_search_invalid_request(client, mock_db_with_data):
    response = client.post(
        "/api/search", json={"query": "短", "top_k": 0, "min_similarity": 0.0}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "invalid request data" in data["error"]
    assert data["detail"] is not None


def test_search_fail(client, mock_db_with_data, monkeypatch):
    def mock_search_judgments_fail(query, top_k, min_similarity):
        raise Exception("Search error")

    monkeypatch.setattr(search, "search_judgments", mock_search_judgments_fail)
    response = client.post(
        "/api/search",
        json={"query": "測試搜尋服務崩潰", "top_k": 10, "min_similarity": 0.0},
    )
    assert response.status_code == 500
    data = response.get_json()
    assert "Search error" in data["error"]
    assert data["detail"] is None

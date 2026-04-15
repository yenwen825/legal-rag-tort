import pytest
import sqlite3
from models import database
from models.database import get_db
import json
import numpy as np
from api import judgment


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


def test_judgment(client, mock_db_with_data):
    response = client.get("/api/judgment/1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == 1
    assert data["title"] == "案由"
    assert data["case_number"] == "112年度訴字第972號"
    assert data["court"] == "臺灣新北地方法院"
    assert data["date"] == "20210615"
    assert data["compensation"] == 200000
    assert data["facts"] == "事實"
    assert data["reasoning"] == "理由"
    assert data["decision"] == "主文"
    assert data["full_text"] == "判決全文"
    assert data["evidence_types"] == ["定位截圖", "錄影畫面", "現場照片"]


def test_judgment_not_found(client, mock_db_with_data):
    response = client.get("/api/judgment/999")
    assert response.status_code == 404
    data = response.get_json()
    assert "judgment not found" in data["error"]
    assert data["detail"] is None


def test_judgment_id_type_error(client):
    response = client.get("/api/judgment/型別測試")
    assert response.status_code == 404


def test_judgment_fail(client, monkeypatch):
    def mock_get_judgment_by_id_fail(id):
        raise Exception("Judgment error")

    monkeypatch.setattr(judgment, "get_judgment_by_id", mock_get_judgment_by_id_fail)
    response = client.get("/api/judgment/1")
    assert response.status_code == 500
    data = response.get_json()
    assert "internal server error" in data["error"]
    assert data["detail"] is None

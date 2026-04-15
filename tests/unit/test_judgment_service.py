import pytest
import sqlite3
from models import database
from models.database import get_db
import json
from services.judgment_service import get_judgment_by_id


def test_get_judgment_by_id(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE judgments (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, case_number TEXT, court TEXT, date TEXT, compensation INTEGER, facts TEXT, reasoning TEXT, decision TEXT, full_text TEXT, evidence_types TEXT)"
        )
        cursor.execute(
            "INSERT INTO judgments (title, case_number, court, date, compensation, facts, reasoning, decision, full_text, evidence_types) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
            ),
        )

    response = get_judgment_by_id(1)
    assert response is not None
    assert response.id == 1
    assert response.title == "案由"
    assert response.case_number == "112年度訴字第972號"
    assert response.court == "臺灣新北地方法院"
    assert response.date == "20210615"
    assert response.compensation == 200000
    assert response.facts == "事實"
    assert response.reasoning == "理由"
    assert response.decision == "主文"
    assert response.full_text == "判決全文"
    assert response.evidence_types == ["定位截圖", "錄影畫面", "現場照片"]

    with pytest.raises(ValueError):
        get_judgment_by_id(2)

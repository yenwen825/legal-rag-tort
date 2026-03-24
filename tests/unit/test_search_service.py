from services import search_service
from services.search_service import search_judgments
import numpy as np
from models import database
from models.database import get_db
import sqlite3
import json

def test_search_judgments_parameters(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE judgments (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, case_number TEXT, court TEXT, date TEXT, compensation INTEGER, facts TEXT, reasoning TEXT, decision TEXT, evidence_types TEXT, vector BLOB)")
        cursor.execute("INSERT INTO judgments (title, case_number, court, date, compensation, facts, reasoning, decision, evidence_types, vector) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("案由1", "案號1", "臺灣新北地方法院", "20210615", 100000, "事實1", "理由1", "主文1", json.dumps(["定位截圖","錄影畫面","現場照片"]), np.random.rand(1536).astype(np.float32).tobytes()))
        cursor.execute("INSERT INTO judgments (title, case_number, court, date, compensation, facts, reasoning, decision, evidence_types, vector) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("案由2", "案號2", "臺灣新北地方法院", "20210615", 200000, "事實2", "理由2", "主文2", json.dumps(["定位截圖","錄影畫面","現場照片"]), np.random.rand(1536).astype(np.float32).tobytes()))
        cursor.execute("INSERT INTO judgments (title, case_number, court, date, compensation, facts, reasoning, decision, evidence_types, vector) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("案由3", "案號3", "臺灣臺中地方法院", "20210615", 300000, "事實3", "理由3", "主文3", json.dumps(["定位截圖","錄影畫面","現場照片"]), np.random.rand(1536).astype(np.float32).tobytes()))   
        cursor.execute("INSERT INTO judgments (title, case_number, court, date, compensation, facts, reasoning, evidence_types, vector) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", ("none", "none", "none", "none", 0, "none", "none", "none", np.empty(1536, dtype=np.float32).tobytes()))    
    monkeypatch.setattr(search_service, "get_vector_cache", lambda: (np.array([1, 2, 3]), np.random.rand(3, 1536).astype(np.float32)))
    monkeypatch.setattr(search_service, "query_embeddings", lambda x: np.random.rand(1536).astype(np.float32))
    query = "配偶透過交友軟體認識網友，兩人多次相約去汽車旅館休息，原告握有發票、信用卡刷卡紀錄以及汽車旅館的監視器畫面"
    top_k = 10
    min_similarity = 0.3
    response = search_judgments(query, top_k, min_similarity)
    assert response is not None
    assert response.query == query
    assert len(response.results) <= top_k
    for r in response.results:
        assert r.similarity >= min_similarity


def test_search_judgments_no_result(monkeypatch):
    monkeypatch.setattr(search_service, "get_vector_cache", lambda: (np.array([]), np.empty((0, 1536))))
    monkeypatch.setattr(search_service, "query_embeddings", lambda x: None)
    response = search_judgments("配偶透過交友軟體認識網友，兩人多次相約去汽車旅館休息，原告握有發票、信用卡刷卡紀錄以及汽車旅館的監視器畫面", 10, 0.5)
    assert response.model_dump()["results"] == []
    assert response.model_dump()["stats"] == {"total": 0, "median_compensation": 0, "avg_compensation": 0.0, "min_compensation": 0, "max_compensation": 0}
    assert response.model_dump()["query"] == "配偶透過交友軟體認識網友，兩人多次相約去汽車旅館休息，原告握有發票、信用卡刷卡紀錄以及汽車旅館的監視器畫面"


def test_search_judgments_stats(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    monkeypatch.setattr(search_service, "get_vector_cache", lambda: (np.array([1, 2, 3]), np.random.rand(3, 1536).astype(np.float32)))
    monkeypatch.setattr(search_service, "query_embeddings", lambda x: np.random.rand(1536).astype(np.float32))

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE judgments (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, case_number TEXT, court TEXT, date TEXT, compensation INTEGER, facts TEXT, reasoning TEXT, decision TEXT, evidence_types TEXT, vector BLOB)")
        cursor.execute("INSERT INTO judgments (title, case_number, court, date, compensation, facts, reasoning, decision, evidence_types, vector) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("案由1", "案號1", "臺灣新北地方法院", "20210615", 100000, "事實1", "理由1", "主文1", json.dumps(["定位截圖","錄影畫面","現場照片"]), np.random.rand(1536).astype(np.float32).tobytes()))
        cursor.execute("INSERT INTO judgments (title, case_number, court, date, compensation, facts, reasoning, decision, evidence_types, vector) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("案由2", "案號2", "臺灣新北地方法院", "20210615", 200000, "事實2", "理由2", "主文2", json.dumps(["定位截圖","錄影畫面","現場照片"]), np.random.rand(1536).astype(np.float32).tobytes()))
        cursor.execute("INSERT INTO judgments (title, case_number, court, date, compensation, facts, reasoning, decision, evidence_types, vector) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("案由3", "案號3", "臺灣臺中地方法院", "20210615", 300000, "事實3", "理由3", "主文3", json.dumps(["定位截圖","錄影畫面","現場照片"]), np.random.rand(1536).astype(np.float32).tobytes()))   
        cursor.execute("INSERT INTO judgments (title, case_number, court, date, compensation, facts, reasoning, evidence_types, vector) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", ("none", "none", "none", "none", 0, "none", "none", "none", np.empty(1536, dtype=np.float32).tobytes()))    
    response = search_judgments("配偶透過交友軟體認識網友，兩人多次相約去汽車旅館休息，原告握有發票、信用卡刷卡紀錄以及汽車旅館的監視器畫面", 10, 0.0)
    assert response.model_dump()["stats"] == {"total": 3, "median_compensation": 200000, "avg_compensation": 200000.0, "min_compensation": 100000, "max_compensation": 300000}
    assert response.model_dump()["query"] == "配偶透過交友軟體認識網友，兩人多次相約去汽車旅館休息，原告握有發票、信用卡刷卡紀錄以及汽車旅館的監視器畫面"

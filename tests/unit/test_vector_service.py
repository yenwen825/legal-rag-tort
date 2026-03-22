from services import vector_service
from services.vector_service import get_vector_cache, clear_vector_cache, load_vector_data, query_embeddings, cosine_similarity
import services.vector_service as vector_service
from models import database
from models.database import get_db
import numpy as np
import sqlite3
import pytest
from unittest.mock import MagicMock, patch

def test_get_vector_cache(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE judgments (id INTEGER PRIMARY KEY AUTOINCREMENT, vector BLOB)")
        vec1 = np.arange(1536, dtype=np.float32)
        vec2 = np.arange(1536, dtype=np.float32) * 2
        vec3 = np.arange(1536, dtype=np.float32) * 3
        cursor.execute("INSERT INTO judgments (vector) VALUES (?)", (vec1.tobytes(),))
        cursor.execute("INSERT INTO judgments (vector) VALUES (?)", (vec2.tobytes(),))
        cursor.execute("INSERT INTO judgments (vector) VALUES (?)", (vec3.tobytes(),))
    clear_vector_cache()
    ids, vector_matrix = get_vector_cache()
    assert ids.shape[0] == 3
    assert vector_matrix.shape[0] == 3
    assert vector_matrix.shape[1] == 1536


def test_clear_vector_cache():
    vector_service._vector_cache = ("ids", "vector_matrix")
    vector_service.clear_vector_cache()
    assert vector_service._vector_cache is None


def test_load_vector_data(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test.db"
    sqlite3.connect(test_db_path).close()
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE judgments (id INTEGER PRIMARY KEY AUTOINCREMENT, vector BLOB)")
        vec1 = np.arange(1536, dtype=np.float32)
        vec2 = np.arange(1536, dtype=np.float32) * 2
        vec3 = np.arange(1536, dtype=np.float32) * 3
        cursor.execute("INSERT INTO judgments (vector) VALUES (?)", (vec1.tobytes(),))
        cursor.execute("INSERT INTO judgments (vector) VALUES (?)", (vec2.tobytes(),))
        cursor.execute("INSERT INTO judgments (vector) VALUES (?)", (vec3.tobytes(),))
    ids, vector_matrix = load_vector_data()
    assert ids.shape[0] == 3
    assert vector_matrix.shape[0] == 3
    assert vector_matrix.shape[1] == 1536

# test query_embeddings
def mock_openai_response(embedding_list):
    mock_res = MagicMock(data=[MagicMock(embedding=embedding_list)])
    return mock_res

@patch('services.vector_service.client.embeddings.create')
def test_query_embeddings_dimension_mismatch(mock_create, caplog):
    mock_create.return_value = mock_openai_response([0.1] * 512)
    result = query_embeddings("wrong dimension")
    assert result is None
    assert "embedding dimension mismatch" in caplog.text

@patch('services.vector_service.client.embeddings.create')
def test_query_embeddings_api_error(mock_create, caplog):
    mock_create.side_effect = Exception("OpenAI API Down")
    result = query_embeddings("api error")
    assert result is None
    assert "Error querying embeddings" in caplog.text


def test_cosine_similarity():
    query_vector = [1, 0]
    vector_matrix = np.array([[1, 0], [1, 1], [1, -1]])
    result = cosine_similarity(query_vector, vector_matrix)
    assert result.shape == (3,)
    assert np.isclose(result[0], 1.0)
    assert np.isclose(result[1], 0.70710678)
    assert np.isclose(result[2], 0.70710678)

    
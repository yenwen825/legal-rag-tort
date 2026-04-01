from hashlib import sha256
import numpy as np
import logging
from openai import OpenAI
from models.database import get_db
from dotenv import load_dotenv
import os
from typing import Optional
from services.redis_client import get_redis_client

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
# ===== vector cache (module-level variable) =====
_vector_cache = None  # (ids, vector_matrix)

def get_vector_cache():
    global _vector_cache
    if _vector_cache is None:
        _vector_cache = load_vector_data()
    
    return _vector_cache

def clear_vector_cache():
    global _vector_cache
    _vector_cache = None
    logging.info("vector cache cleared")

def load_vector_data():
    """
    load all vectors from the database, and directly form a NumPy matrix (without list)
    
    returns:
        tuple: (ids, vector_matrix)
            ids: np.ndarray - shape (N,), database IDs
            vector_matrix: np.ndarray - shape (N, 1536), float32 vector matrix
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, vector FROM judgments ORDER BY id")
        rows = cursor.fetchall()
    
    n_rows = len(rows)
    
    if n_rows == 0:
        logging.warning("no judgment data in the database")
        return np.array([]), np.array([]).reshape(0, 1536)
    
    # pre-allocate memory: (N, 1536) matrix
    vector_matrix = np.empty((n_rows, 1536), dtype=np.float32)
    ids = np.empty(n_rows, dtype=np.int32)
    
    # fill the matrix row by row: directly convert the BLOB to a NumPy array
    for i, row in enumerate(rows):
        ids[i] = row['id']
        # convert the BLOB to a float32 array (length 1536)
        vector_matrix[i] = np.frombuffer(row['vector'], dtype=np.float32)
    
    logging.info(f"loaded {n_rows} vectors, matrix shape: {vector_matrix.shape}")
    
    return ids, vector_matrix 

def query_embeddings(query: str) -> Optional[np.array]:
    """
    args:
        text: str
    returns:
        list of floats (1536 dimension vector)
    """
    redis_client = get_redis_client()
    hash_key = sha256(query.encode()).hexdigest()
    if redis_client is not None:
        try:
            embedding = redis_client.get(f"embedding:{hash_key}")
            if embedding is not None:
                return np.frombuffer(embedding, dtype=np.float32)
        except Exception as e:
            logging.warning(f"Error querying embeddings from Redis: {e}")
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
            encoding_format="float"
        )
        embedding = response.data[0].embedding
        if len(embedding) != 1536:
            logging.error(f"embedding dimension mismatch: {len(embedding)} != 1536")
            return None
        embedding_array = np.array(embedding, dtype=np.float32)
        if redis_client is not None:
            try:
                redis_client.setex(f"embedding:{hash_key}", 60 * 60 * 24, embedding_array.tobytes())
            except Exception as e:
                logging.warning(f"Error storing embeddings in Redis: {e}")
        return embedding_array
    except Exception as e:
        logging.error(f"Error querying embeddings: {e}")
        return None


def cosine_similarity(query_vector, vector_matrix):
    """
    args:
        query_vector: np.ndarray - shape (1536,)
        vector_matrix: np.ndarray - shape (N, 1536)
    
    returns:
        np.ndarray - shape (N,), the cosine similarity between the query vector and all the vectors in the vector matrix (0~1)
    """
    dot_product = np.dot(vector_matrix, query_vector)
    query_vector_norm = np.linalg.norm(query_vector)
    vector_matrix_norm = np.linalg.norm(vector_matrix, axis=1)
    similarities = dot_product / (query_vector_norm * vector_matrix_norm)
    return similarities


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 1. cache test
    ids, vector_matrix = get_vector_cache()
    print("ids shape:", ids.shape, "vector_matrix shape:", vector_matrix.shape)

    # 2. query vector test
    q = query_embeddings("配偶與第三人汽車旅館過夜")

    if q is not None:
        print("query vector shape:", q.shape)
        # 3. cosine similarity test
        sims = cosine_similarity(q, vector_matrix)
        print("similarities shape:", sims.shape)
        print("min similarity:", sims.min(), "max similarity:", sims.max())
    
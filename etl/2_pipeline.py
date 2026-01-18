"""
2_pipeline.py
判決資料清洗與向量化管道

流程:
1. 載入 raw/*.json 判決資料
2. 使用 OpenAI 清洗與萃取關鍵資訊 (賠償金額、當事人、證據等)
3. 生成 embedding 向量 (text-embedding-3-small)
4. 儲存到 SQLite (legal_tort.db) 與 Numpy (vectors.npy)
"""

import os
import json
import sqlite3
import numpy as np
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

# 載入環境變數
load_dotenv()

# 初始化 OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


class JudgmentExtracted(BaseModel):
    """萃取的判決結構化資料"""
    title: str
    case_number: str
    court: str
    date: str
    plaintiff: str
    defendant: str
    compensation: Optional[int]
    facts: str
    reasoning: str
    decision: str
    evidence_types: List[str]
    related_case_number: Optional[str]
    is_overturned: bool


def load_raw_judgments() -> List[Dict]:
    """載入 data/raw/ 下的所有判決 JSON"""
    raw_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
    
    if not os.path.exists(raw_dir):
        print(f"❌ 找不到 {raw_dir} 資料夾")
        return []
    
    judgments = []
    
    for filename in os.listdir(raw_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(raw_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    judgments.extend(data)
                else:
                    judgments.append(data)
    
    print(f"✅ 載入 {len(judgments)} 筆原始判決")
    return judgments


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def extract_judgment_info(raw_judgment: Dict) -> Optional[JudgmentExtracted]:
    """
    使用 OpenAI 萃取判決關鍵資訊
    
    Args:
        raw_judgment: 原始判決資料
    
    Returns:
        結構化的判決資料
    """
    # TODO: 實作 OpenAI API 呼叫，使用 structured output
    # 參考: https://platform.openai.com/docs/guides/structured-outputs
    
    pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_embedding(text: str) -> List[float]:
    """
    使用 OpenAI 生成 embedding 向量
    
    Args:
        text: 要向量化的文字
    
    Returns:
        向量 (1536 維)
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def init_database():
    """初始化 SQLite 資料庫"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'legal_tort.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS judgments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            case_number TEXT UNIQUE NOT NULL,
            court TEXT,
            date TEXT,
            plaintiff TEXT,
            defendant TEXT,
            compensation INTEGER,
            facts TEXT,
            reasoning TEXT,
            decision TEXT,
            evidence_types TEXT,
            related_case_number TEXT,
            is_overturned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"✅ 資料庫初始化完成: {db_path}")


def save_to_database(judgments: List[JudgmentExtracted], vectors: np.ndarray):
    """
    儲存判決到資料庫與向量檔案
    
    Args:
        judgments: 判決資料列表
        vectors: 對應的向量矩陣
    """
    db_path = os.path.join(os.path.dirname(__file__), '..', 'legal_tort.db')
    vectors_path = os.path.join(os.path.dirname(__file__), '..', 'vectors.npy')
    
    # 儲存到 SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for judgment in judgments:
        cursor.execute('''
            INSERT OR REPLACE INTO judgments 
            (title, case_number, court, date, plaintiff, defendant, 
             compensation, facts, reasoning, decision, evidence_types, 
             related_case_number, is_overturned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            judgment.title,
            judgment.case_number,
            judgment.court,
            judgment.date,
            judgment.plaintiff,
            judgment.defendant,
            judgment.compensation,
            judgment.facts,
            judgment.reasoning,
            judgment.decision,
            json.dumps(judgment.evidence_types, ensure_ascii=False),
            judgment.related_case_number,
            1 if judgment.is_overturned else 0
        ))
    
    conn.commit()
    conn.close()
    
    # 儲存向量
    np.save(vectors_path, vectors)
    
    print(f"✅ 已儲存 {len(judgments)} 筆判決到資料庫")
    print(f"✅ 已儲存向量矩陣: {vectors.shape}")


def main():
    """主程式"""
    print("=" * 50)
    print("Legal RAG Tort - 資料清洗與向量化管道")
    print("=" * 50)
    
    # 1. 初始化資料庫
    init_database()
    
    # 2. 載入原始判決
    raw_judgments = load_raw_judgments()
    
    if not raw_judgments:
        print("❌ 沒有找到原始判決資料，請先執行 1_fetch_data.py")
        return
    
    # 3. 萃取與向量化
    print("\n開始處理判決...")
    extracted_judgments = []
    vectors = []
    
    for raw in tqdm(raw_judgments, desc="處理中"):
        try:
            # 萃取資訊
            extracted = extract_judgment_info(raw)
            if not extracted:
                continue
            
            # 生成向量 (使用 facts 欄位)
            vector = generate_embedding(extracted.facts)
            
            extracted_judgments.append(extracted)
            vectors.append(vector)
            
        except Exception as e:
            print(f"❌ 處理失敗: {e}")
            continue
    
    # 4. 儲存
    if extracted_judgments:
        vectors_array = np.array(vectors)
        save_to_database(extracted_judgments, vectors_array)
        print(f"\n✅ 完成！共處理 {len(extracted_judgments)} 筆判決")
    else:
        print("❌ 沒有成功處理任何判決")


if __name__ == "__main__":
    main()

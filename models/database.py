"""
Database Connection Module
資料庫連線管理

負責：
- 管理 SQLite 連線
- 提供資料庫操作的基礎設定
"""

import sqlite3
import os
from contextlib import contextmanager


# 資料庫路徑（專案根目錄下的 legal_tort.db）
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'legal_tort.db'
)


def get_db_connection() -> sqlite3.Connection:
    """
    建立資料庫連線
    
    Returns:
        sqlite3.Connection: SQLite 連線物件
        
    配置：
        - Row factory 設為 sqlite3.Row（可用欄位名稱存取）
        - 啟用外鍵約束
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 讓查詢結果可以用欄位名稱存取
    conn.execute('PRAGMA foreign_keys = ON')  # 啟用外鍵約束
    return conn


@contextmanager
def get_db():
    """
    Context manager 提供資料庫連線
    
    使用方式:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM judgments")
            results = cursor.fetchall()
    
    優點：
        - 自動關閉連線
        - 異常時自動 rollback
        - 正常結束時自動 commit
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """
    初始化資料庫（檢查表是否存在）
    
    注意：
        - 實際的表結構已由 etl/pipeline.py 建立
        - 這裡只做驗證，不重新建立
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 檢查 judgments 表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='judgments'
        """)
        
        if cursor.fetchone() is None:
            raise RuntimeError(
                "資料庫表不存在！請先執行 ETL pipeline (etl/pipeline.py)"
            )
        
        # 檢查資料筆數
        cursor.execute("SELECT COUNT(*) as count FROM judgments")
        count = cursor.fetchone()['count']
        
        return {
            'status': 'ok',
            'total_judgments': count
        }


def get_db_stats() -> dict:
    """
    目的：health check 用
    取得資料庫統計資訊
    
    Returns:
        dict: 包含資料庫統計的字典
            - total_judgments: 總判決數
            - total_compensations: 有賠償金額的判決數
            - avg_compensation: 平均賠償金額
            - db_size_mb: 資料庫檔案大小 (MB)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 總判決數
        cursor.execute("SELECT COUNT(*) as count FROM judgments")
        total = cursor.fetchone()['count']
        
        # 有賠償的判決數（排除 0）
        cursor.execute("SELECT COUNT(*) as count FROM judgments WHERE compensation > 0")
        total_compensations = cursor.fetchone()['count']
        
        # 平均賠償金額
        cursor.execute("SELECT AVG(compensation) as avg FROM judgments WHERE compensation > 0")
        avg_comp = cursor.fetchone()['avg']
        
        # 資料庫檔案大小
        db_size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
        db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
        
        return {
            'total_judgments': total,
            'total_compensations': total_compensations,
            'avg_compensation': round(avg_comp) if avg_comp else 0,
            'db_size_mb': db_size_mb
        }


if __name__ == '__main__':
    """測試資料庫連線"""
    print("Testing database connection...")
    print(f"Database path: {DB_PATH}")
    
    try:
        stats = init_db()
        print(f"✅ Database initialized: {stats}")
        
        db_stats = get_db_stats()
        print("📊 Database stats:")
        print(f"   - Total judgments: {db_stats['total_judgments']}")
        print(f"   - With compensation: {db_stats['total_compensations']}")
        print(f"   - Avg compensation: NT$ {db_stats['avg_compensation']:,}")
        print(f"   - Database size: {db_stats['db_size_mb']} MB")
        
    except Exception as e:
        print(f"❌ Error: {e}")

"""
1_fetch_data.py
從司法院判決書公開資料庫下載民國 113-114 年判決書，其中與侵害配偶權相關判決大約 2000 筆)
"""

import os
import json
import requests
from typing import List, Dict
from tqdm import tqdm
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


def fetch_judgments(year: int, month: int = None, keyword: str = "侵害配偶權") -> List[Dict]:
    """
    用 py script 讀取 data/raw 下的判決資料
    
    Args:
        year: 民國年份 (例如 113, 114)
        keyword: 搜尋關鍵字
    
    Returns:
        判決資料列表
    """
    # TODO: 
    
    print(f"正在下載 {year} 年 {month} 月的判決資料...")
    
    judgments = []

    # ...
    
    return judgments


def save_to_file(judgments: List[Dict], filename: str):
    """
    將判決資料儲存為 JSON 檔案
    
    Args:
        judgments: 判決資料列表
        filename: 檔案名稱
    """
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(judgments, f, ensure_ascii=False, indent=2)
    
    print(f"已儲存 {len(judgments)} 筆判決到 {output_path}")


def main():
    """主程式"""
    print("=" * 50)
    print("Legal RAG Tort - 判決資料下載工具")
    print("=" * 50)
    
    # 下載民國 113 年判決
    judgments_113 = fetch_judgments(year=113)
    if judgments_113:
        save_to_file(judgments_113, "judgments_113.json")
    
    # 下載民國 114 年判決
    judgments_114 = fetch_judgments(year=114)
    if judgments_114:
        save_to_file(judgments_114, "judgments_114.json")
    
    total = len(judgments_113) + len(judgments_114)
    print(f"\n✅ 下載完成！共 {total} 筆判決")


if __name__ == "__main__":
    main()

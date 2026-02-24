# for one time migration to add full_text column to the database
import sqlite3
import json
import os
import logging


logging.basicConfig(level=logging.INFO)

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(base_dir, 'legal_tort.db')

JSON_PATH = os.path.join(base_dir, 'data', 'judgments_all_spouse_tort.json')

def add_full_text():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(judgments)")
    columns_info = cursor.fetchall()
    current_columns = [info[1] for info in columns_info]
    if 'full_text' not in current_columns:
        logging.info("欄位不存在，新增full_text 欄位")
        cursor.execute('''
            ALTER TABLE judgments ADD COLUMN full_text TEXT
        ''')
        conn.commit()
        logging.info("full_text 欄位新增成功")
    else:
        logging.info("full_text 欄位已存在，跳過操作")

    conn.close()

def load_from_json():
    logging.info(f"載入 JSON 檔案: {JSON_PATH}")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    logging.info(f"載入 {len(data)} 筆判決")

    return data

def update_full_text(data):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    updated_count = 0
    not_found_count = 0

    for item in data:
        year = item['JYEAR']
        case = item['JCASE']
        no = item['JNO']
        case_number = f"{year}年度{case}字第{no}號"
        court = item['JFULL'].split('\n')[0].strip().split('民事判決')[0].strip()

        cursor.execute('''
            UPDATE judgments SET full_text = ? WHERE case_number = ? AND court = ?
        ''', (item['JFULL'], case_number, court))
        if cursor.rowcount > 0:
            updated_count += 1
        else:
            not_found_count += 1

    logging.info(f"full_text 更新完成，成功 {updated_count} 筆，未匹配 {not_found_count} 筆")

    conn.commit()
    conn.close()

def main():
    logging.info("開始新增 full_text 欄位")
    add_full_text()
    data = load_from_json()
    update_full_text(data)
    logging.info("所有判決的 full_text 更新完成")

if __name__ == "__main__":
    main()
import os
import sqlite3
import pandas as pd
import json
from datetime import datetime


def export_to_excel():
    """匯出資料庫到 Excel"""
    # 資料庫路徑
    db_path = os.path.join(os.path.dirname(__file__), "..", "legal_tort.db")

    # 連接資料庫
    conn = sqlite3.connect(db_path)

    # 讀取資料（不包含 vector 欄位，因為是二進位資料）
    query = """
        SELECT 
            id,
            title,
            case_number,
            court,
            date,
            compensation,
            facts,
            reasoning,
            decision,
            evidence_types,
            created_at
        FROM judgments
        ORDER BY id
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # 處理 evidence_types（從 JSON 字串轉為易讀格式）
    df["evidence_types"] = df["evidence_types"].apply(
        lambda x: ", ".join(json.loads(x)) if x else ""
    )

    # 匯出檔案路徑
    output_dir = os.path.join(os.path.dirname(__file__), "..", "exports")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"judgments_{timestamp}.xlsx")

    # 匯出到 Excel
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="判決資料", index=False)

        # 調整欄位寬度
        worksheet = writer.sheets["判決資料"]
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter

            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception:
                    pass

            # 設定欄位寬度（最大 50，最小 10）
            adjusted_width = min(max(max_length, 10), 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    print("✅ 匯出完成！")
    print(f"📁 檔案位置: {output_file}")
    print(f"📊 共匯出 {len(df)} 筆判決")

    return output_file


if __name__ == "__main__":
    export_to_excel()

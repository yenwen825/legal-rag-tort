import os
import json
import logging
from typing import List, Dict
from pathlib import Path
from datetime import datetime


# 配置 logging
def setup_logging():
    """配置日誌系統"""
    log_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
    )
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(
        log_dir, f"fetch_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    # 同時輸出到檔案和終端
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    return log_file


def check_keyword_match(text: str) -> bool:
    """
    先檢查必要關鍵字 "侵害配偶權"，避免重複搜尋
    """
    if "侵害配偶權" not in text:
        return False

    return "民法第184" in text or "民法第1056" in text


def find_spouse_tort_judgments(json_dir: str) -> List[Dict]:
    """
    在 JSON 檔案中搜尋侵害配偶權相關的判決
    只處理路徑中包含「民事」的資料夾，忽略刑事等其他資料夾

    Args:
        json_dir: JSON 檔案所在的資料夾

    Returns:
        侵害配偶權判決列表
    """
    judgments = []
    json_files = list(Path(json_dir).rglob("*.json"))
    failed_files = []

    for json_path in json_files:
        # 只處理路徑中包含「民事」的檔案
        if "民事" not in str(json_path):
            continue

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 檢查 JTITLE (案由) 和 JFULL (判決全文)
            title = data.get("JTITLE", "")
            full_text = data.get("JFULL", "")
            combined_text = title + full_text

            if check_keyword_match(combined_text):
                judgments.append(data)

        except Exception as e:
            failed_files.append((json_path.name, str(e)))
            continue

    # 顯示錯誤統計
    if failed_files:
        failure_rate = len(failed_files) / len(json_files) * 100 if json_files else 0
        logging.warning(f"{len(failed_files)} 個檔案讀取失敗 ({failure_rate:.2f}%)")

        # 少量失敗時顯示詳細資訊（方便除錯）
        if len(failed_files) <= 5:
            for filename, error in failed_files:
                logging.error(f"  - {filename}: {error}")
        elif len(failed_files) <= 20:
            # 中等數量只顯示檔名
            for filename, error in failed_files[:5]:
                logging.error(f"  - {filename}")
            logging.warning(f"  ... 還有 {len(failed_files) - 5} 個")

    return judgments


def main():
    """主程式：處理 2024/01 到 2025/10 的所有判決"""
    # 設定日誌
    log_file = setup_logging()

    logging.info("=" * 70)
    logging.info("Legal RAG Tort - 侵害配偶權判決篩選 (2024/01-2025/10)")
    logging.info("=" * 70)
    logging.info(f"日誌檔案: {log_file}")

    # 設定路徑
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    extracted_base = os.path.join(base_dir, "data", "extracted")
    output_file = os.path.join(base_dir, "data", "judgments_all_spouse_tort.json")

    # 檢查 extracted 資料夾是否存在
    if not os.path.exists(extracted_base):
        logging.error("找不到 data/extracted/ 資料夾")
        logging.error("請先解壓縮 RAR 檔案到 data/extracted/")
        return

    # 掃描所有月份資料夾（202401-202510）
    month_folders = sorted(
        [
            f
            for f in os.listdir(extracted_base)
            if os.path.isdir(os.path.join(extracted_base, f))
            and (f.startswith("2024") or f.startswith("2025"))
        ]
    )

    if not month_folders:
        logging.error("找不到任何月份資料夾（202401-202510）")
        return

    logging.info(f"找到 {len(month_folders)} 個月份: {', '.join(month_folders)}")

    # 處理每個月份
    all_judgments = []
    total_json_count = 0
    progress_file = output_file.replace(".json", "_progress.json")

    for i, month in enumerate(month_folders, 1):
        month_dir = os.path.join(extracted_base, month)
        logging.info(f"處理 {month}... ({i}/{len(month_folders)})")

        # 搜尋侵害配偶權判決（自動忽略非民事資料夾）
        judgments = find_spouse_tort_judgments(month_dir)

        # 統計
        json_count = len(list(Path(month_dir).rglob("*.json")))
        total_json_count += json_count
        all_judgments.extend(judgments)

        logging.info(f"  → 找到 {len(judgments)} 筆")

        # 每月儲存進度（防止中斷損失）
        os.makedirs(os.path.dirname(progress_file), exist_ok=True)
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "processed_months": i,
                    "last_month": month,
                    "total_judgments": len(all_judgments),
                    "judgments": all_judgments,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    # 檢查結果
    if not all_judgments:
        logging.error("所有月份都沒有找到符合條件的判決")
        if os.path.exists(progress_file):
            os.remove(progress_file)
        return

    # 儲存正式版
    logging.info("儲存最終結果...")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_judgments, f, ensure_ascii=False, indent=2)

    # 刪除進度檔
    if os.path.exists(progress_file):
        os.remove(progress_file)

    # 最終總結
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    logging.info("=" * 70)
    logging.info("✅ 完成")
    logging.info("=" * 70)
    logging.info(f"處理月份: {len(month_folders)} 個")
    logging.info(f"總 JSON: {total_json_count:,}")
    logging.info(f"侵害配偶權判決: {len(all_judgments):,} 筆")
    logging.info(f"檔案大小: {file_size_mb:.1f} MB")
    logging.info(f"篩選率: {len(all_judgments) / total_json_count * 100:.2f}%")
    logging.info(f"輸出: {output_file}")
    logging.info("下一步: python etl/pipeline.py")


if __name__ == "__main__":
    main()

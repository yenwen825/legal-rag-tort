# for one time data migration to fix court names in the database
import logging
from etl.court_parser import get_court
from models.database import get_db

logging.basicConfig(level=logging.INFO)

def fix_court_names():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, case_number, full_text, court FROM judgments")
        judgments = cursor.fetchall()
        total_count = len(judgments)
        fixed_count = 0
        skipped_count = 0
        for judgment in judgments:
            if not judgment['full_text']:
                logging.warning(f"Full text is empty for judgment {judgment['case_number']}")
                skipped_count += 1
                continue
            court = get_court(judgment['full_text'], judgment['case_number'])
            if court != judgment['court']:
                cursor.execute("UPDATE judgments SET court = ? WHERE id = ?", (court, judgment['id']))
                logging.info(f"Court name for judgment {judgment['case_number']} fixed from {judgment['court']} to {court}")
                fixed_count += 1
        logging.info(f"total {total_count} judgments, Court names fixed successfully: {fixed_count} judgments, {skipped_count} judgments skipped because full text is empty")

def main():
    logging.info("Starting court names fix...")
    fix_court_names()
    logging.info("Court names fix completed")

if __name__ == "__main__":
    main()
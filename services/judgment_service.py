from models.database import get_db
from models.schemas import JudgmentDetail
import json


def get_judgment_by_id(id: int) -> JudgmentDetail:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, case_number, court, date, compensation, facts, reasoning, decision, full_text, evidence_types FROM judgments WHERE id = ?",
            (id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"Judgment with id {id} not found")
        else:
            return JudgmentDetail(
                id=row["id"],
                title=row["title"],
                case_number=row["case_number"],
                court=row["court"],
                date=row["date"],
                compensation=row["compensation"],
                facts=row["facts"],
                reasoning=row["reasoning"],
                decision=row["decision"],
                full_text=row["full_text"],
                evidence_types=json.loads(row["evidence_types"])
                if row["evidence_types"]
                else None,
            )

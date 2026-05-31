from services.vector_service import (
    query_embeddings,
    get_vector_cache,
    cosine_similarity,
)
from models.schemas import JudgmentResult, SearchResponse, CompensationStats
from models.database import get_db
import statistics
import json
import cohere
from dotenv import load_dotenv
import os

load_dotenv()

cohere_client = cohere.ClientV2(os.getenv("COHERE_API_KEY"))


def rerank_judgments(
    judgments: list[JudgmentResult], query: str, final_top_k: int = 10
) -> list[JudgmentResult]:
    docs = []
    for judgment in judgments:
        docs.append(
            f"案件事實: {judgment.facts}\n\n判決理由: {judgment.reasoning}\n\n證據: {judgment.evidence_types}"
        )
    ranked_docs = cohere_client.rerank(
        model="rerank-multilingual-v3.0",
        query=query,
        documents=docs,
        top_n=final_top_k,
    )
    ranked_judgments = []
    for ranked_doc in ranked_docs.results:
        ranked_judgments.append(judgments[ranked_doc.index])
    return ranked_judgments


def search_judgments(
    query: str,
    first_top_k: int = 20,
    final_top_k: int = 10,
    min_similarity: float = 0.0,
) -> SearchResponse:
    ids, vector_matrix = get_vector_cache()
    q_embedding = query_embeddings(query)
    if q_embedding is None:
        return SearchResponse(
            results=[],
            stats=CompensationStats(
                total=0,
                median_compensation=0,
                avg_compensation=0,
                min_compensation=0,
                max_compensation=0,
            ),
            query=query,
            search_time_ms=0,
        )
    sims = cosine_similarity(q_embedding, vector_matrix)
    if len(sims) == 0 or sims.max() < min_similarity:
        return SearchResponse(
            results=[],
            stats=CompensationStats(
                total=0,
                median_compensation=0,
                avg_compensation=0,
                min_compensation=0,
                max_compensation=0,
            ),
            query=query,
            search_time_ms=0,
        )
    top_k_idx = sims.argsort()[-first_top_k:][::-1]
    top_k_ids = ids[top_k_idx].tolist()

    placeholder = ", ".join(["?"] * len(top_k_ids))

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, title, case_number, court, date, compensation, facts, reasoning, decision, evidence_types FROM judgments WHERE id IN ({placeholder})",
            top_k_ids,
        )
        rows = cursor.fetchall()

    results = []
    id_to_row = {row["id"]: row for row in rows}

    for i, jid in enumerate(top_k_ids):
        row = id_to_row[jid]
        results.append(
            JudgmentResult(
                id=jid,
                title=row["title"],
                case_number=row["case_number"],
                court=row["court"],
                date=row["date"],
                compensation=row["compensation"],
                facts=row["facts"],
                reasoning=row["reasoning"],
                evidence_types=json.loads(row["evidence_types"])
                if row["evidence_types"]
                else None,
                similarity=sims[top_k_idx[i]],
            )
        )

    reranked_judgments = rerank_judgments(results, query, final_top_k)
    compensations = []
    for judgment in reranked_judgments:
        compensations.append(judgment.compensation)

    response = SearchResponse(
        results=reranked_judgments,
        stats=CompensationStats(
            total=len(compensations),
            median_compensation=int(statistics.median(compensations)),
            avg_compensation=statistics.mean(compensations),
            min_compensation=min(compensations),
            max_compensation=max(compensations),
        ),
        query=query,
        search_time_ms=0,
    )

    return response


if __name__ == "__main__":
    query = "老公多次和小三外出逛街，沒有證據證明性行為，但是有對話紀錄截圖和相擁照片"
    first_top_k = 20
    final_top_k = 10
    min_similarity = 0.0
    response = search_judgments(query, first_top_k, final_top_k, min_similarity)

    print(f"查詢: {response.query}")
    print(f"結果數: {len(response.results)}")
    print(f"統計: {response.stats.model_dump()}")
    print("-" * 60)
    for i, r in enumerate(response.results, 1):
        print(f"\n【第 {i} 筆】 id={r.id} 相似度={r.similarity:.4f}")
        print(f"  標題: {r.title}")
        print(f"  案號: {r.case_number} | 法院: {r.court}")
        print(f"  賠償: {r.compensation} 元")
        print(f"  案情摘要: {r.facts}")
        print(f"  論述摘要: {r.reasoning}")
        if r.evidence_types:
            print(f"  證據類型: {', '.join(r.evidence_types)}")

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import List, Optional, Union, Dict, Any


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="案情描述，至少 5 個字",
    )
    top_k: int = Field(
        20, ge=1, le=50, description="回傳最相似的前 N 筆判決，預設 20 筆"
    )
    min_similarity: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="最小相似度分數，預設為 0.0，表示不限制相似度分數",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "配偶與第三人多次在汽車旅館過夜，有監視器影像和信用卡簽單",
                "top_k": 20,
                "min_similarity": 0.0,
            }
        }
    )

    @field_validator("query")
    def query_not_empty(v: str) -> str:
        if not v.strip():
            raise ValueError("query cannot be empty")
        return v.strip()


class JudgmentResult(BaseModel):
    """single judgment search result"""

    id: int = Field(..., description="判決資料庫 ID")
    title: str = Field(..., description="判決標題")
    case_number: str = Field(..., description="案號")
    court: str = Field(..., description="法院名稱")
    date: Optional[str] = Field(None, description="判決日期")
    compensation: int = Field(..., description="賠償金額（新臺幣）")
    facts: str = Field(..., description="案情摘要")
    reasoning: str = Field(..., description="法院論述摘要")
    evidence_types: Optional[List[str]] = Field(None, description="證據類型清單")
    similarity: float = Field(..., ge=0.0, le=1.0, description="相似度分數 (0-1)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 123,
                "title": "侵權行為損害賠償",
                "case_number": "110年度侵字第123號",
                "court": "臺灣臺北地方法院",
                "date": "20210615",
                "compensation": 150000,
                "facts": "被告與配偶多次在汽車旅館過夜...",
                "reasoning": "依原告提出之監視器影像、信用卡簽單...",
                "evidence_types": ["監視器影像", "信用卡簽單", "通訊軟體對話"],
                "similarity": 0.87,
            }
        }
    )


class CompensationStats(BaseModel):
    total: int = Field(..., ge=0, description="搜尋結果總數")
    median_compensation: int = Field(..., description="中位數賠償金額")
    avg_compensation: float = Field(..., description="平均賠償金額")
    min_compensation: int = Field(..., description="最低賠償金額")
    max_compensation: int = Field(..., description="最高賠償金額")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 10,
                "median_compensation": 120000,
                "avg_compensation": 135500.0,
                "min_compensation": 50000,
                "max_compensation": 300000,
            }
        }
    )


class SearchResponse(BaseModel):
    results: List[JudgmentResult] = Field(..., description="判決搜尋結果清單")
    stats: CompensationStats = Field(..., description="賠償金額統計")
    query: str = Field(..., description="原始查詢內容（echo back）")
    search_time_ms: Optional[int] = Field(None, description="搜尋耗時（毫秒）")

    @model_validator(mode="after")
    def check_results_and_stats(self):
        if len(self.results) != self.stats.total:
            raise ValueError("length of results and stats.total should be consistent")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "id": 123,
                        "title": "損害賠償",
                        "case_number": "112年度訴字第971號",
                        "court": "臺灣臺北地方法院",
                        "date": "20210615",
                        "compensation": 150000,
                        "facts": "被上訴人與甲○○於100年9月14日結婚，婚後育有3名未成年子女。甲○○自000年0月間多次藉故晚歸、行蹤不明......",
                        "reasoning": "原證2、5、6應有證據能力，因為被上訴人為維護自身配偶權而拍攝取證，取得之行為非以強暴或脅迫等方式為之，且夫妻違反忠誠義務行為證據取得極為困難......",
                        "evidence_types": [
                            "LINE對話截圖",
                            "監視錄影畫面",
                            "用餐照片",
                            "行車紀錄器影片",
                        ],
                        "similarity": 0.87,
                    },
                    {
                        "id": 224,
                        "title": "侵權行為損害賠償",
                        "case_number": "112年度訴字第972號",
                        "court": "臺灣新北地方法院",
                        "date": "20210615",
                        "compensation": 10000,
                        "facts": "甲○○與配偶丙○○於民國101年11月17日結婚，乙○○與丙○○為同事，自109年12月中旬起至000年0月00日間交往並發生多次性行為，乙○○明知......",
                        "reasoning": "本院認為，配偶應互負誠實之義務，乙○○與丙○○之交往及性行為已足以破壞甲○○之婚姻生活，且情節重大，故甲○○請求乙○○賠償精神慰撫金有據。乙○○主張配偶權非憲法或法律上權利，顯無足採。......",
                        "evidence_types": [
                            "戶口名簿影本",
                            "對話紀錄",
                            "請假紀錄",
                            "證人證詞",
                        ],
                        "similarity": 0.85,
                    },
                ],
                "stats": {
                    "total": 2,
                    "median_compensation": 120000,
                    "avg_compensation": 135500.0,
                    "min_compensation": 50000,
                    "max_compensation": 300000,
                },
                "query": "配偶與第三人多次在汽車旅館過夜",
                "search_time_ms": 245,
            }
        }
    )


class JudgmentDetail(BaseModel):
    """full judgment details"""

    id: int = Field(..., description="判決資料庫 ID")
    title: str = Field(..., description="判決標題")
    case_number: str = Field(..., description="案號")
    court: str = Field(..., description="法院名稱")
    date: Optional[str] = Field(None, description="判決日期")
    compensation: int = Field(..., description="賠償金額（新臺幣）")
    facts: str = Field(..., description="事實摘要")
    reasoning: str = Field(..., description="理由摘要")
    decision: str = Field(..., description="判決主文")
    full_text: str = Field(..., description="判決全文")
    evidence_types: Optional[List[str]] = Field(None, description="證據類型清單")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 123,
                "title": "侵權行為損害賠償",
                "case_number": "110年度侵字第123號",
                "court": "臺灣臺北地方法院",
                "date": "20210615",
                "compensation": 150000,
                "facts": "被上訴人與甲○○於100年9月14日結婚，婚後育有3名未成年子女。甲○○自000年0月間多次藉故晚歸、行蹤不明......",
                "reasoning": "因為被上訴人為維護自身配偶權而拍攝取證，取得之行為非以強暴或脅迫等方式為之，且夫妻違反忠誠義務行為證據取得極為困難......",
                "decision": "被告應給付原告新臺幣壹拾伍萬元...",
                "full_text": "臺灣桃園地方法院民事判決\r\n108年度婚字第201號\r\n109年度婚字第460號\r\n原      告  甲○○  住○○市○○區○○○路0段......",
                "evidence_types": ["監視器影像", "信用卡簽單"],
            }
        }
    )


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="服務狀態")
    database: dict = Field(..., description="資料庫狀態")
    vector_cache_status: str = Field(..., description="向量快取狀態")
    vector_cache_count: int = Field(..., description="向量快取筆數")
    redis: str = Field(..., description="Redis 狀態")
    version: str = Field(..., description="API 版本")
    timestamp: str = Field(..., description="檢查時間")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "database": {
                    "total_judgments": 10000,
                    "total_compensations": 1000,
                    "avg_compensation": 100000,
                    "db_size_mb": 100,
                },
                "vector_cache_status": "loaded",
                "vector_cache_count": 100,
                "redis": "ok",
                "version": "1.0.0",
                "timestamp": "2024-01-01T12:00:00",
            }
        }
    )


class ErrorResponse(BaseModel):
    error: str = Field(..., description="錯誤訊息")
    detail: Optional[Union[str, List[Dict[str, Any]]]] = Field(
        None, description="詳細錯誤資訊（字串或 Pydantic 驗證錯誤 list）"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "查詢內容不能為空白",
                "detail": "請輸入至少 5 個字的案情描述",
            }
        }
    )


class AnalysisRequest(BaseModel):
    query: str = Field(..., description="使用者的查詢情境")
    result_ids: List[int] = Field(
        ..., description="要進行分析的判決 ID 列表 (通常為 Top 5)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "原告懷疑被告外遇，長期gps定位被告的車，發現被告多次出入汽車旅館，法院是否會採用此證據作為判斷侵害配偶權之依據",
                "result_ids": [683, 1, 589, 1317, 1406],
            }
        }
    )


class AnalysisResponse(BaseModel):
    summary: str = Field(..., description="針對查詢的情境，基於判決全文產生的分析總結")
    analysis_time_ms: int = Field(..., description="分析耗時（毫秒）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "summary": "法院對於原告使用GPS定位追蹤被告的行為及其所獲得的證據的採納，將依據證據的合法性及其對隱私權的影響進行評估...",
                "analysis_time_ms": 19949,
            }
        }
    )

import os
import json
import sqlite3
import logging
import re
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

# 載入環境變數
load_dotenv()

# 初始化 OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


# 配置 logging
def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    # 同時輸出到檔案和終端
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return log_file


class GPTExtractedData(BaseModel):
    """GPT 萃取的判決資訊（用於 OpenAI Structured Output）"""
    compensation: int = Field(
        0,
        description="""
        原告因侵害配偶權獲得的精神慰撫金（新臺幣）。
        規則：
        1. 連帶賠償：記錄連帶金額（原告最多獲得該金額）
        2. 單一被告：記錄該金額
        3. 有其他獨立請求：只記錄侵害配偶權部分
        4. 有反訴抵銷：記錄抵銷前原始金額
        5. 不包含利息、訴訟費用
        6. 如原告敗訴或全部駁回：填 0
        """
    )
    facts: str = Field(
        ...,
        description="""
        摘要判決書中的核心案情（事實段落），包括：
        1. 外遇具體互動行為（例如：共宿、親密接觸、通訊內容、互動頻率）
        2. 關鍵時間、地點
        3. 原告發現經過
        4. 關鍵證據內容（例如：照片、通訊記錄、GPS定位、證人證詞）
        
        要求：
        - 以精煉的方式描述，保留所有關鍵細節
        - 移除程序性語言（例如「本院審理後」「經調查」等）
        - 使用客觀第三人稱敘述
        - 長度控制在 500-1000 字
        - 用於語義搜尋，需包含足夠的關鍵字和上下文
        
        ⚠️ 重要：只摘要判決書中實際記載的內容，絕對不可添加、推測或想像任何資訊。
        """
    )
    reasoning: str = Field(
        ...,
        description="""
        摘要法院的核心法律論述（主要來自「得心證之理由」段落），包括：
        1. 證據能力之審查（如法院有討論證據是否具證據能力、是否可採、證明力強弱等論述）
        2. 法院如何認定被告行為是否構成侵害配偶權（包含事實認定過程、證據取捨理由）
        3. 法院對於兩造主張及抗辯是否採信之理由
        4. 法院如何評估侵害行為的嚴重程度（情節是否重大）
        5. 法院如何判斷賠償金額的適當性
        6. 引用的特別法律條文或判例（僅限法院有特別解釋論述者）
        
        ⚠️ 應避免摘要的常見法條（這些幾乎每個判決都有，無特別意義）：
        - 民法第 184 條第 1 項：「因故意或過失，不法侵害他人之權利者，負損害賠償責任」
        - 民法第 185 條：「數人共同不法侵害他人之權利者，連帶負損害賠償責任」
        - 民法第 195 條：「不法侵害他人之身體、健康、名譽...得請求賠償相當之金額」
        - 除非法院針對這些法條有進一步的解釋或特別論述，否則不需摘要
        
        要求：
        - 重點摘要「得心證之理由」段落的核心論證過程
        - 保留法院的論述邏輯與推理過程
        - 移除冗長的程序性描述
        - 長度控制在 300-600 字
        
        ⚠️ 重要：只摘要判決書中實際記載的內容，不可添加法院未提及的論述或見解。
        """
    )
    evidence_types: List[str] = Field(
        default_factory=list,
        description="""
        判決中提到的證據類型列表。
        
        要求：
        1. 必須明確、具體，避免模糊描述
        2. ❌ 禁止使用：「其他」、「其他相關證據」、「其他證據」等無具體內容的描述
        
        範例：
        - ✅ 可接受：通訊記錄（LINE對話截圖）
        - ✅ 可接受：照片
        - ✅ 可接受：汽車旅館住宿記錄
        - ✅ 可接受：GPS定位記錄
        - ✅ 可接受：證人證詞
        - ✅ 可接受：手機翻拍畫面
        - ✅ 可接受：影片
        - ✅ 可接受：信用卡簽帳單
        - ❌ 禁止：其他
        - ❌ 禁止：其他相關證據
        - ❌ 禁止：其他證據
        
        ⚠️ 只列出判決中實際提及的證據類型，不可臆測或添加判決中未提及的證據。
        """
    )


class JudgmentExtracted(BaseModel):
    # 基本資訊
    title: str
    case_number: str
    court: str
    date: str

    # 核心搜尋維度
    compensation: int  # 賠償金額（0 表示原告敗訴/無賠償）
    facts: str
    reasoning: str
    decision: str
    full_text: str
    evidence_types: List[str]


def load_raw_judgments() -> List[Dict]:
    base_dir = os.path.join(os.path.dirname(__file__), '..')
    judgment_file = os.path.join(base_dir, 'data', 'judgments_all_spouse_tort.json')
    
    if not os.path.exists(judgment_file):
        logging.error(f"找不到判決檔案: {judgment_file}")
        logging.error(f"請先執行 etl/fetch_data.py")
        return []
    
    try:
        with open(judgment_file, 'r', encoding='utf-8') as f:
            judgments = json.load(f)
        
        logging.info(f"載入 {len(judgments)} 筆原始判決")
        return judgments
    except Exception as e:
        logging.error(f"載入判決檔案失敗: {e}")
        return []


def get_court(jfull: str, case_number: str) -> str:
        # 取得法院名稱
        # 臺灣臺中地方法院臺中簡易庭小額民事判決 >>> 臺灣臺中地方法院
        # 臺灣桃園地方法院民事簡易判決 >>> 臺灣桃園地方法院
        # 臺灣臺北地方法院簡易民事判決 >>> 臺灣臺北地方法院
        # 臺灣高等法院臺中分院民事判決 >>> 臺灣高等法院臺中分院
        # 臺灣南投地方法院民事裁定 >>> 臺灣南投地方法院
        # 5臺灣桃園地方法院民事簡易判決 >>> 臺灣桃園地方法院
        #「宣示判決筆錄」 >>> 臺灣板橋地方法院（例：112年度板簡字第1751號）
        # 目前無法處理：「臺灣○○地方法院」（113年度訴字第369號）、「智慧財產與商業法院」
        first_line = jfull.split('\n')[0].strip()
        court_pattern = r'^.*?(臺灣|福建|最高).*?(法院.*?分院|法院)'
        match = re.search(court_pattern, first_line)
        if match:
            court = match.group(0)
        else:
            match = re.search(r"宣[\s\u3000]*示[\s\u3000]*判[\s\u3000]*決[\s\u3000]*筆[\s\u3000]*錄", first_line)
            if match:
                pattern = r"中[\s\u3000]*華[\s\u3000]*民[\s\u3000]*國.*?日([\s\S]{0,100}?)書[\s\u3000]*記[\s\u3000]*官"
                blocks = re.findall(pattern, jfull)
                court = None
                for block in reversed(blocks):
                    if "法院" in block:
                        raw_court_line = block.strip()
                        clean_match = re.search(court_pattern, raw_court_line)
                        court = clean_match.group(0) if clean_match else raw_court_line
                        break  
                if not court:
                    logging.warning(f"宣示判決筆錄找不到法院名稱: {case_number}")
                    court = first_line  
            else:
                logging.warning(f"無法萃取法院名稱: {case_number}")
                court = first_line  
        return court


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def extract_judgment_info(raw_judgment: Dict) -> Optional[JudgmentExtracted]:
    try:
        # ===== 階段 1：直接從 JSON 取得基本資訊 =====
        title = raw_judgment.get('JTITLE', '').strip()
        date = raw_judgment.get('JDATE', '').strip()
        
        # 組合案號：{JYEAR}年度{JCASE}字第{JNO}號
        jyear = raw_judgment.get('JYEAR', '').strip()
        jcase = raw_judgment.get('JCASE', '').strip()
        jno = raw_judgment.get('JNO', '').strip()
        case_number = f"{jyear}年度{jcase}字第{jno}號"
        
        # 取得判決全文
        jfull = raw_judgment.get('JFULL', '').strip()
        if not jfull:
            logging.warning(f"判決內容為空: {case_number}")
            return None
        
        # ===== 長度監控（記錄但不截斷）=====
        text_length = len(jfull)
        estimated_tokens = text_length * 3  # 中文字保守估計為 3 tokens
        
        if estimated_tokens > 100000:
            logging.info(
                f"⚠️  判決 {case_number} 較長 "
                f"({text_length:,} 字, 約 {estimated_tokens:,} tokens)"
            )
        
        if estimated_tokens > 125000:
            logging.warning(
                f"⚠️⚠️  判決 {case_number} 非常長 "
                f"({text_length:,} 字, 約 {estimated_tokens:,} tokens)，"
                f"接近 gpt-4o-mini 的 128K token 限制，可能會被截斷或失敗"
            )
        
        court = get_court(jfull, case_number)
 
        # 取得判決主文（從「主文」到「事實」之間的內容）
        # 使用正則表達式匹配，允許「主文」和「事實」中間有空格或全形空格
        decision = ""
        main_pattern = r'主[\s　]*文'  # 匹配「主文」「主　文」「主    文」等
        fact_pattern = r'事[\s　]*實'  # 匹配「事實」「事　實」「事    實」等
        
        main_match = re.search(main_pattern, jfull)
        fact_match = re.search(fact_pattern, jfull)
        
        if main_match and fact_match:
            start = main_match.start()
            end = fact_match.start()
            if end > start:
                decision = jfull[start:end].strip()
        
        if not decision:
            logging.warning(f"無法萃取判決主文: {case_number}")
            # 不 return None，繼續處理其他欄位
        
        # ===== 階段 2：用 GPT-4o-mini 萃取判決內容 =====
        system_prompt = """你是在台灣執業的資深家事律師，專精於侵害配偶權案件。
請從判決書中萃取資訊，並以繁體中文回答。
各欄位的詳細說明已在 JSON Schema 中定義，請嚴格遵守。

⚠️ 重要原則：
- 只摘要判決書中實際記載的內容
- 不可添加、推測、想像或編造任何資訊
- 如果判決書中沒有明確記載某項資訊，請如實反映
- 這是法律文件，準確性至關重要

📋 特別注意事項：

1. 【reasoning 欄位】：
   - 重點摘要「得心證之理由」段落
   - 如有討論證據能力、證據可採性等論述，應納入摘要
   - 避免摘要常見請求權基礎法條（民法 184、185、195 條），除非法院有特別論述
   - 專注於法院的論證過程、事實認定理由、證據取捨理由

2. 【evidence_types 欄位】：
   - 必須具體明確，禁止使用「其他」、「其他相關證據」等模糊描述
   - 只列出判決中實際提及的證據類型
   - 例如：「通訊記錄（LINE對話截圖）」、「汽車旅館住宿記錄」、「GPS定位記錄」、「手機翻拍畫面」等"""
        
        user_prompt = f"""請萃取以下判決書的資訊：{jfull}"""
        
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=GPTExtractedData,
            temperature=0.1  # 降低隨機性，提高一致性
        )
        
        gpt_data = response.choices[0].message.parsed
        
        if not gpt_data:
            logging.warning(f"GPT 萃取失敗: {case_number}")
            return None
        
        # ===== 階段 3：組合結果 =====
        return JudgmentExtracted(
            title=title,
            case_number=case_number,
            court=court,
            date=date,
            compensation=gpt_data.compensation,
            facts=gpt_data.facts,
            reasoning=gpt_data.reasoning,
            decision=decision,  # 直接從 JFULL 切割取得
            full_text=jfull,  
            evidence_types=gpt_data.evidence_types
        )
        
    except Exception as e:
        logging.error(f"萃取判決資訊時發生錯誤: {e}")
        if 'case_number' in locals():
            logging.error(f"問題案號: {case_number}")
        return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_embedding(judgment: JudgmentExtracted) -> Optional[List[float]]:
    """
    使用 OpenAI text-embedding-3-small 生成語義向量
    
    向量化的內容：
    - 案情摘要 (facts)
    - 法律論述 (reasoning)
    - 證據類型 (evidence_types)
    
    註：不包含 title，因為大部分侵害配偶權案件的案由都是
    「侵權行為損害賠償」等相似標題，對語義搜尋無幫助。
    
    模型選擇：text-embedding-3-small (1536 維)
    - 成本：$0.020 / 1M tokens
    - 精度：足夠用於 2,000 筆判決的語義搜尋
    - Token 限制：8,191 tokens (遠大於實際需求 ~5,000 tokens)
    
    Args:
        judgment: 已萃取的判決結構化資料
    
    Returns:
        向量 (1536 維)，若失敗則回傳 None
    """
    try:
        # ===== 組合向量化文字 =====
        embedding_text = f"""案情摘要：
{judgment.facts}

法律論述：
{judgment.reasoning}

證據類型：{', '.join(judgment.evidence_types) if judgment.evidence_types else '無'}"""
        
        # ===== 文字長度檢查 =====
        # text-embedding-3-small 最多支援 8191 tokens
        # 粗估：1 中文字 ≈ 2-3 tokens，保守估計為 3
        estimated_tokens = len(embedding_text) * 3
        
        if estimated_tokens > 8000:
            logging.warning(
                f"案號 {judgment.case_number} 的文字過長 "
                f"(約 {estimated_tokens} tokens)，將被截斷"
            )
            # OpenAI 會自動截斷，但我們記錄警告
        
        # ===== 呼叫 OpenAI API =====
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=embedding_text,
            encoding_format="float"  # 明確指定浮點數格式
        )
        
        embedding = response.data[0].embedding
        
        # ===== 驗證向量維度 =====
        if len(embedding) != 1536:
            logging.error(
                f"案號 {judgment.case_number} 的向量維度異常: "
                f"{len(embedding)} (預期 1536)"
            )
            return None
        
        return embedding
        
    except Exception as e:
        logging.error(
            f"生成向量時發生錯誤 (案號: {judgment.case_number}): {e}"
        )
        return None


def init_database():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'legal_tort.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS judgments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            case_number TEXT NOT NULL,
            court TEXT NOT NULL,
            date TEXT,
            compensation INTEGER NOT NULL DEFAULT 0,
            facts TEXT NOT NULL,
            reasoning TEXT NOT NULL,
            decision TEXT NOT NULL,
            full_text TEXT,
            evidence_types TEXT,
            vector BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(case_number, court)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    logging.info(f"資料庫初始化完成: {db_path}")


def save_to_database(judgments: List[JudgmentExtracted], vectors: List[List[float]]):
    db_path = os.path.join(os.path.dirname(__file__), '..', 'legal_tort.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    inserted_count = 0
    ignored_count = 0
    
    for judgment, vector in zip(judgments, vectors):
        # 將向量轉為 float32 並序列化為二進位
        vector_blob = np.array(vector, dtype=np.float32).tobytes()
        
        cursor.execute('''
            INSERT OR IGNORE INTO judgments 
            (title, case_number, court, date, compensation, 
             facts, reasoning, decision, full_text, evidence_types, vector)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            judgment.title,
            judgment.case_number,
            judgment.court,
            judgment.date,
            judgment.compensation,
            judgment.facts,
            judgment.reasoning,
            judgment.decision,
            judgment.full_text,
            json.dumps(judgment.evidence_types, ensure_ascii=False),
            vector_blob
        ))
        
        # 檢查是否成功插入
        if cursor.rowcount > 0:
            inserted_count += 1
        else:
            ignored_count += 1
            logging.warning(
                f"⚠️  跳過重複判決: {judgment.case_number} ({judgment.court})"
            )
    
    conn.commit()
    conn.close()
    
    logging.info(f"✅ 已儲存 {inserted_count} 筆判決到資料庫（含向量）")
    if ignored_count > 0:
        logging.warning(f"⚠️  跳過 {ignored_count} 筆重複判決")


def main():
    """main function (supports batch saving and checkpoint resume)"""
    # 設定日誌
    log_file = setup_logging()
    
    logging.info("=" * 70)
    logging.info("Legal RAG Tort - 資料清洗與向量化管道")
    logging.info("=" * 70)
    logging.info(f"日誌檔案: {log_file}")
    
    # 1. 初始化資料庫
    init_database()
    
    # 2. 載入原始判決
    raw_judgments = load_raw_judgments()
    
    if not raw_judgments:
        logging.error("沒有找到原始判決資料，請先執行 etl/fetch_data.py")
        return
    
    logging.info(f"📊 載入 {len(raw_judgments)} 筆判決")

    # raw_judgments = raw_judgments[:10]
    # logging.info(f"⚠️  測試模式：只處理前 {len(raw_judgments)} 筆")
    
    # 3. 設定進度檔案路徑
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    progress_file = os.path.join(base_dir, 'data', 'pipeline_progress.json')
    
    # 4. 檢查是否有未完成的進度
    start_index = 0
    total_processed = 0
    failed_count = 0
    
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                start_index = progress_data.get('last_index', 0)
                total_processed = progress_data.get('total_processed', 0)
                failed_count = progress_data.get('failed_count', 0)
            
            logging.info(f"📂 發現進度檔案，從第 {start_index + 1} 筆繼續處理...")
            logging.info(f"📊 已處理 {total_processed} 筆，失敗 {failed_count} 筆")
        except Exception as e:
            logging.warning(f"讀取進度檔案失敗: {e}，將從頭開始")
            start_index = 0
            total_processed = 0
            failed_count = 0
    
    # 5. 萃取與向量化（批次處理）
    logging.info(f"開始處理判決（總共 {len(raw_judgments)} 筆）...")
    
    if start_index > 0:
        logging.info(f"⏭️  跳過前 {start_index} 筆判決（從進度檔案讀取）")
    
    BATCH_SIZE = 50  # 每 50 筆存檔一次
    batch_judgments = []
    batch_vectors = []
    
    # 從 start_index 開始處理（切片），並讓 enumerate 從正確的索引開始
    for idx, raw in enumerate(
        tqdm(
            raw_judgments[start_index:], 
            desc="處理中",
            total=len(raw_judgments),      # 分母：總判決數
            initial=start_index             # 起始值：從 start_index 開始顯示
        ), 
        start=start_index
    ):
        try:
            # 萃取資訊
            extracted = extract_judgment_info(raw)
            if not extracted:
                failed_count += 1
                continue
            
            # 生成向量
            vector = generate_embedding(extracted)
            if not vector:
                failed_count += 1
                logging.warning(f"向量生成失敗: {extracted.case_number}")
                continue
            
            batch_judgments.append(extracted)
            batch_vectors.append(vector)
            total_processed += 1
            
            # 每處理 BATCH_SIZE 筆就存檔一次
            if len(batch_judgments) >= BATCH_SIZE:
                save_to_database(batch_judgments, batch_vectors)
                
                logging.info(f"💾 已儲存批次 ({len(batch_judgments)} 筆)，累計: {total_processed} 筆")
                
                # 儲存進度（輕量化：只記錄 last_index 和統計資料）
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'last_index': idx + 1,
                        'total_processed': total_processed,
                        'failed_count': failed_count
                    }, f, ensure_ascii=False, indent=2)
                
                # 清空批次緩存
                batch_judgments = []
                batch_vectors = []
            
        except Exception as e:
            failed_count += 1
            logging.warning(f"處理失敗: {e}")
            continue
    
    # 6. 儲存最後一批（如果有剩餘）
    if batch_judgments:
        save_to_database(batch_judgments, batch_vectors)
        logging.info(f"💾 已儲存最後批次 ({len(batch_judgments)} 筆)")
    
    # 7. 刪除進度檔案（全部完成）
    if os.path.exists(progress_file):
        os.remove(progress_file)
        logging.info("🗑️  已刪除進度檔案")
    
    # 8. 輸出統計
    logging.info("=" * 70)
    logging.info("✅ 完成")
    logging.info("=" * 70)
    logging.info(f"成功處理: {total_processed} 筆")
    logging.info(f"失敗: {failed_count} 筆")
    logging.info(f"成功率: {total_processed / len(raw_judgments) * 100:.2f}%")


if __name__ == "__main__":
    main()

from models.schemas import SearchResponse
from models.database import get_db
from dotenv import load_dotenv
from openai import OpenAI
import os
from services.redis_client import get_redis_client
from hashlib import sha256
import logging

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def analyze(query: str, result_ids: list[int]):
    if not result_ids or not query:
        return None
    top_k = 5
    judgment_ids = [str(jid) for jid in result_ids][:top_k]
    
    cache_string = f"{query}|{','.join(judgment_ids)}"
    hash_key = sha256(cache_string.encode()).hexdigest()
    
    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            generation = redis_client.get(f"generation:{hash_key}")
            if generation is not None:
                return generation.decode('utf-8')
        except Exception as e:
            logging.warning(f"Error querying generation from Redis: {e}")
    
    # get full text by judgment id
    placeholders = ",".join(["?"] * len(judgment_ids))
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT id, full_text FROM judgments WHERE id IN ({placeholders})", 
                judgment_ids
            )
            rows = cursor.fetchall()
            id_to_fulltext = {str(row['id']): row['full_text'] for row in rows}
    except Exception as e:
        logging.error(f"Error querying DB for full_text: {e}")
        return None

    context_blocks = []
    MAX_CHARS = 15000  
    
    for i, jid in enumerate(judgment_ids, 1):
        ft = id_to_fulltext.get(jid, "無全文資料")
        
        if len(ft) > MAX_CHARS:
            # 智慧截斷：台灣判決的開頭通常是當事人姓名、居住地與訴訟代理人等無用資訊。
            # 真正的內文通常從「事實及理由」或「理由」開始。我們嘗試尋找這些關鍵字來跳過開頭。
            start_idx = ft.find('事實及理由')
            if start_idx == -1:
                start_idx = ft.find('理由\n') 
            if start_idx == -1:
                start_idx = 0  # 找不到就從頭開始

            ft_core = ft[start_idx:]
            
            # 經過濾除開頭後，如果還是太長（遇到極端長文），再進行去中保頭尾
            # 保留前 6000 字（通常包含原被告主張）與最後 9000 字（通常包含得心證之理由）
            if len(ft_core) > MAX_CHARS:
                ft_core = ft_core[:6000] + "\n\n...(因文章過長，此處省略部分內文)...\n\n" + ft_core[-9000:]
            
            ft = ft_core
            
        context_blocks.append(f"===判決 {i} 開始===\n{ft}\n===判決 {i} 結束===")
        
    context_str = "\n\n".join(context_blocks)

    try:
        system_prompt = """你是一位專精於台灣家事法的資深律師。
你的任務是根據【參考判決】，針對【情境查詢】給出專業的實務分析。

【嚴格遵守規則】：
1. 絕不捏造（Zero Hallucination）：所有的分析、金額、法理見解，必須「完全」來自於提供的判決書內容。
2. 案件獨立性：請注意區分不同判決的情境與判賠金額，絕對不可將 A 案的事實與 B 案的賠償金額張冠李戴。
3. 切題回答：使用專業的法律邏輯分析，重點聚焦在回答情境查詢，說明法院的核心見解、潛在風險、影響賠償金額的因素。
4. 具體分析：不要泛泛地總結判決文的共同點。也不要空泛的說考量雙方身分地位、經濟狀況、精神痛苦程度、行為情節重大等因素，請指出導致金額加重或減輕的具體事實。
5. 輸出限制：請直接以一段話敘述，限制在 200 字以內的繁體中文。不要重述情境查詢的內容，不要有任何開場白。
"""

        user_prompt = f"""【情境查詢】：{query}

參考以下 {len(judgment_ids)} 篇相關民事判決全文：

{context_str}

=================================
再次提醒【情境查詢】：{query}
=================================

綜合上述多篇判決內容，針對【情境查詢】，給出一份專業的法院見解總結與風險分析。"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        generation = response.choices[0].message.content
        
        if redis_client is not None:
            try:
                redis_client.set(f"generation:{hash_key}", generation, ex=86400)
            except Exception as e:
                logging.warning(f"Error setting generation in Redis: {e}")
                
        return generation
    except Exception as e:
        logging.error(f"Error analyzing query: {e}")
        return None
    
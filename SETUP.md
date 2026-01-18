# 快速設定指引

## 📋 步驟 1: 建立 .env 檔案

由於 `.env` 檔案包含敏感資訊（API Key），需要手動建立：

```bash
# 在專案根目錄建立 .env 檔案
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-api-key-here
SECRET_KEY=dev-secret-key-change-in-production
EOF
```

或直接建立檔案並編輯：

```bash
touch .env
```

然後在 `.env` 中填入：

```
OPENAI_API_KEY=sk-你的OpenAI金鑰
SECRET_KEY=隨機字串用於Flask加密
```

## 📋 步驟 2: 建立虛擬環境 (建議)

```bash
# 建立虛擬環境
python3 -m venv venv

# 啟動虛擬環境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

## 📋 步驟 3: 安裝套件

```bash
pip install -r requirements.txt
```

## 📋 步驟 4: 準備原始判決資料

從司法院判決書系統手動下載民國 113-114 年的侵害配偶權判決，並將 JSON 檔案放到 `data/raw/` 資料夾。

例如：
```
data/raw/judgments_113.json
data/raw/judgments_114.json
```

或其他命名的 JSON 檔案（ETL 會自動讀取 `data/raw/` 下所有 `.json` 檔案）

**提示**: 可將多個 JSON 檔案放入同一資料夾，系統會自動合併處理。

## 📋 步驟 5: 執行資料清洗與向量化

```bash
python etl/2_pipeline.py
```

這會產生：
- `legal_tort.db` (SQLite 資料庫)
- `vectors.npy` (向量檔案)

## 📋 步驟 6: 啟動應用

完成資料處理後，啟動 Flask 應用：

```bash
python app.py
```

開啟瀏覽器前往: **http://localhost:5000**

## 🎉 完成！

現在你可以：
1. 在搜尋框輸入案情描述
2. 點擊「搜尋相似判決」
3. 查看 AI 返回的 10 個最相似判決
4. 參考賠償金額統計
5. 點擊「查看全文」查看判決詳情

## ⚠️ 常見問題

### Q1: OpenAI API Key 在哪裡取得？

前往 [OpenAI Platform](https://platform.openai.com/api-keys) 註冊並建立 API Key。

### Q2: ETL 流程會花多少時間？

- **準備資料**: 手動下載並上傳到 `data/raw/`
- **2_pipeline.py**: 約 30-60 分鐘（需要呼叫 OpenAI API 處理每筆判決，處理約 2,000 筆）

### Q3: 會產生多少 API 費用？

假設處理 2,000 筆判決：
- **萃取資訊** (gpt-4o-mini): 約 $3-5 USD
- **生成向量** (text-embedding-3-small): 約 $0.3-0.5 USD
- **搜尋時生成摘要**: 每次搜尋約 $0.01 USD

總計首次建置約 **$3-6 USD**，後續使用成本極低。

### Q4: 可以不用 OpenAI 嗎？

可以，但需要自行實作：
1. 判決資料清洗邏輯（取代 OpenAI structured output）
2. 向量生成（可使用開源模型如 sentence-transformers）
3. 摘要生成（可使用開源 LLM）

### Q5: 資料庫在哪裡？

- **legal_tort.db**: SQLite 資料庫，包含所有判決結構化資料
- **vectors.npy**: Numpy 陣列，包含所有判決的向量表示

兩者必須配對使用（row index 對應）。

## 🔧 開發模式

啟動 Flask 開發伺服器（會自動重載）：

```bash
export FLASK_ENV=development
python app.py
```

## 🚀 生產部署

使用 Gunicorn (已包含在 requirements.txt)：

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

有問題？請參考 [README.md](README.md) 或提出 Issue！

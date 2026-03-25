# Legal RAG Tort - 侵害配偶權判決 AI 檢索系統

⚡ 為執業律師打造的智慧判決檢索系統，5 秒內找到最相似的侵害配偶權判決

## 🎯 產品特色

- **快速檢索**: 5 秒內返回 10 個相似判決 (vs 傳統關鍵字搜尋 30 分鐘)
- **精準匹配**: 基於 AI 語義相似度，而非傳統的關鍵字搜尋
- **賠償參考**: 自動統計相似案件的賠償金額區間 (中位數、平均數、最高、最低)
- **風險提示**: 清楚標示被上訴審推翻的判決，避免引用瑕疵見解
- **智慧摘要**: AI 自動生成判決與查詢的相似點說明

## 🛠️ 技術架構

- **Backend**: Python + Flask
- **Database**: SQLite (`legal_tort.db`)
- **Vector Search**: Numpy (`vectors.npy`)
- **LLM**: OpenAI API (gpt-4o-mini, text-embedding-3-small)
- **Frontend**: Bootstrap 5 + Jinja2 Templates

## 📁 專案結構

```
legal-rag-tort/
├── .env                    # OpenAI API Key (需自行建立)
├── .gitignore              
├── README.md               
├── requirements.txt        
├── app.py                  # Flask 主程式
├── legal_tort.db           # SQLite 資料庫 (執行 ETL 後產生)
├── vectors.npy             # 向量檔案 (執行 ETL 後產生)
├── templates/
│   └── index.html          # 前端介面
├── data/
│   └── raw/                # 原始判決 JSON (手動上傳)
└── etl/
    ├── fetch_data.py       # 讀取處理判決資料
    ├── pipeline.py         # 資料清洗與向量化
    └── export_to_excel.py  # 匯出 Excel（可選）
```

## 🚀 快速開始

### 1. 安裝依賴套件

建議先建立虛擬環境：

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

安裝套件：

```bash
pip install -r requirements.txt
```

### 2. 設定 OpenAI API Key

建立 `.env` 檔案並填入必要環境變數：

```bash
OPENAI_API_KEY=sk-your-api-key-here
SECRET_KEY=dev-secret-key-change-in-production
```

### 3. 準備原始判決資料

#### Step 1: 上傳判決資料

從司法院判決書系統手動下載民國 113-114 年的侵害配偶權判決，並將 JSON 檔案放到 `data/raw/` 資料夾。

例如：
- `data/raw/judgments_113.json`
- `data/raw/judgments_114.json`

#### Step 2: 清洗與向量化

```bash
python etl/pipeline.py
```

這會:
- 讀取 `data/raw/` 下所有的 JSON 檔案
- 使用 OpenAI 萃取判決關鍵資訊 (賠償金額、當事人、證據等)
- 生成 embedding 向量
- 儲存到 `legal_tort.db` 與 `vectors.npy`

### 4. 啟動 Web 應用

```bash
python app.py
```

開啟瀏覽器前往: `http://localhost:5000`

### 5. 開發與部署

開發模式（自動重載）：

```bash
export FLASK_ENV=development
python app.py
```

生產部署（Gunicorn）：

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 💡 使用情境

### 情境 1: 新案件初步評估
```
輸入: "配偶與第三人多次在汽車旅館過夜，有監視器影像、信用卡簽單、親密簡訊"
輸出: 
  - 10 個相似判決
  - 賠償金額範圍 (例: 中位數 15 萬)
  - 快速評估求償區間
```

### 情境 2: 撰寫書狀前準備
```
輸入: "配偶與第三人有親密簡訊，但沒有性行為的直接證據"
輸出:
  - 找到「只有簡訊證據」也勝訴的判決
  - 參考法院對「親密簡訊」的認定標準
```

### 情境 3: 開庭前準備
```
輸入: "被告抗辯原告也有外遇，所以不應賠償"
輸出:
  - 找到類似抗辯的判決
  - 了解法院如何處理「兩邊都有過失」的情況
```

## 📊 資料範圍

- **案件類型**: 侵害配偶權 (民法 §184, §1056Ⅱ)
- **資料來源**: 司法院判決書系統 (手動下載)
- **年份範圍**: 民國 113-114 年
- **判決數量**: 約 2,000 筆
- **資料格式**: JSON 檔案 (放置於 `data/raw/` 資料夾)

## 🔒 注意事項

1. **資料準備**: 需先從司法院判決書系統手動下載判決 JSON 檔案，並放置於 `data/raw/` 資料夾
2. **OpenAI API 費用**: 本專案會呼叫 OpenAI API，首次建置約需 $3-6 USD（處理 2,000 筆判決）
3. **資料更新**: 判決資料需定期手動下載並重新執行 ETL 流程更新
4. **僅供參考**: 本系統提供的結果僅供參考，最終判斷仍需律師專業評估

## 🆘 常見錯誤排除

### 1) `ImportError: No module named 'flask'`

```bash
pip install -r requirements.txt
```

### 2) `openai.error.AuthenticationError`

請檢查 `.env` 的 `OPENAI_API_KEY` 是否正確且可用。

### 3) `sqlite3.OperationalError: no such table`

```bash
python etl/pipeline.py
```

### 4) 搜尋沒有結果

請先確認是否已完成 ETL，並檢查資料筆數：

```bash
python -c "import sqlite3; conn = sqlite3.connect('legal_tort.db'); print(conn.execute('SELECT COUNT(*) FROM judgments').fetchone())"
```

## 📝 License

目前尚未提供 `LICENSE` 檔案；授權條款待補充。

## 👨‍💻 開發者

如有問題或建議，歡迎提出 Issue 或 Pull Request！

---

**Legal RAG Tort** - 讓 AI 成為律師的最佳助手 ⚖️

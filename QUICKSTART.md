# ⚡ 快速開始 (5 分鐘上手)

## 🚀 最快速度啟動

```bash
# 1. 建立並啟動虛擬環境
python3 -m venv venvs
source venv/bin/activate  # macOS/Linux

# 2. 安裝套件
pip install -r requirements.txt

# 3. 建立 .env 檔案
echo "OPENAI_API_KEY=你的金鑰" > .env

# 4. 驗證設置
python verify_setup.py

# 5. 準備原始資料 (首次使用)
# 手動下載判決 JSON 並放到 data/raw/ 資料夾
# 然後執行資料清洗與向量化
python etl/2_pipeline.py    # 處理資料 (30-60分鐘)

# 6. 啟動應用
python app.py
```

開啟瀏覽器: **http://localhost:5000**

---

## 📝 指令速查表

| 指令 | 說明 |
|------|------|
| `python verify_setup.py` | 驗證專案設置 |
| `python etl/2_pipeline.py` | 資料清洗與向量化 (需先手動上傳原始 JSON 到 data/raw/) |
| `python app.py` | 啟動開發伺服器 |
| `gunicorn -w 4 app:app` | 啟動生產伺服器 |

---

## 🎯 核心功能測試

### 測試 1: 基本搜尋
```
輸入: "配偶與第三人在汽車旅館過夜，有信用卡簽單"
預期: 返回 10 個相似判決 + 賠償統計
```

### 測試 2: 證據類型
```
輸入: "只有親密簡訊，沒有性行為證據"
預期: 找到類似證據類型的判決
```

### 測試 3: 賠償評估
```
輸入: "配偶承認外遇，第三人否認"
預期: 顯示賠償金額區間
```

---

## ⚠️ 注意事項

1. **首次使用**: 必須先手動上傳原始判決 JSON 到 `data/raw/`，然後執行 ETL 流程才能使用搜尋功能
2. **API 費用**: ETL 流程會產生約 $3-6 USD 的 OpenAI API 費用（處理 2,000 筆判決）
3. **處理時間**: 處理 2,000 筆判決約需 30-60 分鐘
4. **資料更新**: 需定期手動下載新判決並重新執行 ETL 以更新資料

---

## 🆘 常見錯誤排除

### 錯誤 1: `ImportError: No module named 'flask'`
```bash
# 解決: 安裝套件
pip install -r requirements.txt
```

### 錯誤 2: `openai.error.AuthenticationError`
```bash
# 解決: 檢查 .env 檔案中的 OPENAI_API_KEY
cat .env
```

### 錯誤 3: `sqlite3.OperationalError: no such table`
```bash
# 解決: 執行 ETL 建立資料庫
python etl/2_pipeline.py
```

### 錯誤 4: 搜尋沒有結果
```bash
# 檢查資料庫是否有資料
python -c "import sqlite3; conn = sqlite3.connect('legal_tort.db'); print(conn.execute('SELECT COUNT(*) FROM judgments').fetchone())"
```

---

## 📚 更多資訊

- **完整文件**: [README.md](README.md)
- **詳細設定**: [SETUP.md](SETUP.md)
- **專案架構**: 參見 README.md 的「技術架構」章節

---

**Legal RAG Tort** - 讓律師工作更有效率 ⚖️✨

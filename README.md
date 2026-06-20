# Job Market Intelligence Agent 📊

這是一個新手友善的求職市場分析網頁。貼入 2–5 個相似職缺後，Agent 會整理跨職缺技能需求、必要與加分條件，以及學習優先順序。履歷為選填；提供履歷時，才會根據真實證據分析個人優勢與技能缺口。

> 核心定位：提供市場情報與決策支援，不代寫履歷，也不替使用者捏造經歷。

## 功能

- 同時比較 2–5 個職缺
- 統計重複出現的市場技能
- 區分必要條件、加分條件與需求程度
- 顯示每個技能來自哪些職缺
- 提供各職缺的重要條件摘要
- 選擇性上傳 PDF、DOCX、TXT 履歷
- 只根據履歷證據判斷個人優勢與技能缺口
- 產生學習與作品集優先順序
- 下載 Markdown 市場分析報告
- 使用 Pydantic Structured Outputs 確保結果格式穩定

## 分析流程

```text
貼入 2–5 個職缺
        ↓
標準化並統計技能需求
        ↓
整理市場趨勢與職缺差異
        ↓
選填履歷 → 比對證據與技能缺口
        ↓
產生學習計畫與可下載報告
```

## 開始使用

### 1. 確認 Python

支援 Python 3.9 以上版本：

```bash
python3 --version
```

### 2. 建立並啟用虛擬環境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
```

### 3. 安裝套件

```bash
pip install -r requirements.txt
```

### 4. 設定 Gemini API Key

```bash
cp .env.example .env
```

在 `.env` 填入：

```dotenv
GEMINI_API_KEY=你的_Gemini_API_Key
GEMINI_MODEL=gemini-3.5-flash
```

請到 [Google AI Studio](https://aistudio.google.com/apikey) 免費建立 Gemini API Key。

免費方案有速率限制，而且提交內容可能被 Google 用於改善產品。若要加入履歷，建議先移除姓名、電話、地址等個資。

`.env` 已列入 `.gitignore`，不會被推送到 GitHub。

### 5. 啟動網頁

```bash
streamlit run app.py
```

瀏覽器通常會自動開啟 `http://localhost:8501`。

## 如何使用

1. 選擇要比較的職缺數量。
2. 貼入 2–5 個相似職缺，例如三個 Data Analyst 職缺。
3. 視需要上傳履歷；不傳也能進行市場分析。
4. 點擊「開始市場分析」。
5. 查看熱門技能、職缺差異、個人差距與行動計畫。
6. 下載 Markdown 報告保存結果。

## 執行測試

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

測試不會呼叫 Gemini API，因此不會消耗免費額度。

## 專案結構

```text
.
├── app.py                 # Streamlit 網頁介面
├── src/
│   ├── agent.py           # 市場分析 Prompt 與 Gemini API
│   ├── models.py          # 結構化輸出格式
│   ├── report.py          # Markdown 報告產生器
│   └── resume_parser.py   # PDF、DOCX、TXT 文字解析
├── tests/                 # 自動測試
├── pyproject.toml         # pytest 與 Ruff 設定
├── .env.example           # 環境變數範例
├── requirements.txt       # 正式環境套件
└── requirements-dev.txt   # 測試與程式碼檢查套件
```

## 隱私與限制

- Gemini 免費方案的資料政策不適合敏感履歷，請先移除個資。
- 掃描圖片型 PDF 目前無法辨識，需先進行 OCR。
- 技能需求是根據使用者提供的職缺樣本，不代表完整市場。
- AI 仍可能分類錯誤，重要決策請回頭核對原始職缺。
- 第一版不會自動爬取求職網站，避免違反網站使用條款。

## 後續可擴充

- 儲存不同職位的市場分析
- 比較不同地區或產業
- 加入職缺來源網址與引用
- 產生互動式技能趨勢圖
- Streamlit Community Cloud 部署

## 技術

Python、Streamlit、Google Gemini API、Pydantic、PyPDF、python-docx、pytest。

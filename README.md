# JobFit Agent 🎯

JobFit Agent 是一個新手友善的求職分析網頁。上傳履歷並貼上職缺後，它會根據履歷中的真實證據，整理匹配條件、技能缺口、履歷修改方向與面試題目。

> 核心原則：沒有出現在履歷裡的經歷，不會被當成你具備的能力。

## 功能

- 支援 PDF、DOCX、TXT 履歷
- 產生 0–100 的職缺匹配分數
- 每項符合條件都附上履歷證據
- 區分必要條件、加分條件與技能缺口
- 提供不捏造經歷的履歷修改建議
- 依職缺產生面試題與回答架構
- 使用 Pydantic Structured Outputs，確保回傳格式穩定

## 畫面流程

```text
上傳履歷 + 貼上職缺
          ↓
     解析履歷文字
          ↓
 OpenAI Responses API 分析
          ↓
匹配分數 / 證據 / 缺口 / 面試題
```

## 開始使用

### 1. 確認 Python

支援 Python 3.9 以上版本。終端機輸入：

```bash
python3 --version
```

### 2. 建立虛擬環境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell 請改用：

```powershell
.venv\Scripts\Activate.ps1
```

### 3. 安裝套件

```bash
pip install -r requirements.txt
```

### 4. 設定 API Key

先複製設定範例：

```bash
cp .env.example .env
```

打開 `.env`，將 API Key 填入：

```dotenv
OPENAI_API_KEY=你的_API_Key
OPENAI_MODEL=gpt-5.5
```

請在 [OpenAI API Dashboard](https://platform.openai.com/api-keys) 建立 API Key。API 使用費與 ChatGPT 訂閱分開計算。

`.env` 已列入 `.gitignore`，不要把真正的 API Key 上傳到 GitHub。

### 5. 啟動網頁

```bash
streamlit run app.py
```

瀏覽器通常會自動開啟 `http://localhost:8501`。

## 執行測試

開發用套件與測試：

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

測試不會呼叫 OpenAI API，因此不會產生 API 費用。

## 專案結構

```text
.
├── app.py                 # Streamlit 網頁介面
├── src/
│   ├── agent.py           # Prompt 與 OpenAI API 呼叫
│   ├── models.py          # 結構化輸出格式
│   └── resume_parser.py   # PDF、DOCX、TXT 文字解析
├── tests/                 # 自動測試
├── pyproject.toml         # pytest 與 Ruff 設定
├── .env.example           # 環境變數範例
├── requirements.txt       # 正式環境套件
└── requirements-dev.txt   # 測試與程式碼檢查套件
```

## 推送到 GitHub

請先在 GitHub 建立一個空白 repository，例如 `jobfit-agent`，不要勾選自動建立 README。

接著在本專案資料夾執行：

```bash
git add .
git commit -m "Build JobFit Agent MVP"
git remote add origin https://github.com/你的帳號/jobfit-agent.git
git push -u origin main
```

若目前已經有 `origin`，請使用：

```bash
git remote set-url origin https://github.com/你的帳號/jobfit-agent.git
git push -u origin main
```

## 隱私與限制

- 履歷可能包含個人資料，部署公開網站前應加入登入或資料遮罩。
- 掃描圖片型 PDF 目前無法辨識，需先做 OCR。
- 匹配分數是求職準備參考，不代表錄取機率。
- AI 仍可能判斷錯誤，送出履歷前請自行確認內容。

## 後續可擴充

- 履歷匿名化
- 職缺收藏與比較
- 履歷版本管理
- 模擬面試聊天模式
- Streamlit Community Cloud 部署

## 技術

Python、Streamlit、OpenAI Responses API、Pydantic、PyPDF、python-docx、pytest。

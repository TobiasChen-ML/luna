# Roxy Backend Services

這份文檔描述了 Python 後端服務的架構和實現。

## 服務架構

### Backend Service (Port 8000)
主要對話與平台服務，提供：
- 身份認證與帳號管理
- 對話核心功能 (SSE 流式聊天)
- 媒體生成 (圖片/視頻/語音)
- 通知與推送
- 計費與訂閱

### Factory Service (Port 8001)
內容生成與管理服務，提供：
- Character 管理與生成
- Story 管理與生成
- 媒體任務處理
- Prompt 模板管理
- 管理台 UI

## 核心元能力 (Meta Capabilities)

### 1. 模型供應商抽象
- `backend/app/services/llm/` - LLM 供應商抽象層
- 支持 Novita, Deepseek, OpenAI, Ollama
- 自動 fallback 機制

### 2. 提示詞編排
- `factory/app/routers/prompts.py` - Prompt 管理
- 支持變數注入與模板

### 3. 意圖識別與路由
- `backend/app/services/llm_service.py` - 意圖識別
- JSON 結構化輸出

### 4. 任務生命週期
- `backend/app/services/task_service.py` - 任務管理
- 支持同步/異步操作

### 5. Webhook + Polling
- `backend/app/services/task_registry_service.py` - 任務註冊
- Webhook 優先，輪詢兜底

### 6. SSE 推送
- `backend/app/routers/chat.py` - SSE 聊天流
- 事件類型定義在 `backend/app/core/events.py`

### 7. 存儲與落盤
- SQLite/PostgreSQL 通過 SQLAlchemy
- Redis 熱狀態與廣播
- R2 對象存儲

## 快速開始

### 環境準備
```bash
# 創建 conda 環境
conda create -n roxy python=3.13
conda activate roxy

# 安裝依賴
cd backend && pip install -r requirements.txt
cd ../factory && pip install -r requirements.txt
```

### 啟動服務
```bash
# Windows
development/start-services.bat

# Linux/Mac
bash development/start-services.sh
```

### 環境變數
創建 `.env` 文件：
```
NOVITA_API_KEY=your_key
FAL_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
FIREBASE_PROJECT_ID=your_project
DATABASE_URL=sqlite:///./roxy.db
REDIS_URL=redis://localhost:6379/0
```

## API 文檔

- Backend API: http://localhost:8000/docs
- Factory API: http://localhost:8001/docs

## 目錄結構

```
backend/
├── app/
│   ├── core/           # 配置、異常、事件
│   ├── models/         # Pydantic schemas
│   ├── routers/        # API 路由
│   ├── services/       # 業務服務
│   │   ├── llm/        # LLM 供應商
│   │   └── media/      # 媒體服務
│   └── main.py
├── tests/
├── pyproject.toml
└── requirements.txt

factory/
├── app/
│   ├── routers/        # API 路由
│   ├── services/       # 業務服務
│   ├── models.py       # Pydantic schemas
│   ├── config.py       # 配置
│   └── main.py
├── pyproject.toml
└── requirements.txt
```
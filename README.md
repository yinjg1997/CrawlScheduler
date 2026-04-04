# CrawlScheduler

一个基于 FastAPI 和 Vue 3 的爬虫任务调度平台，类似 Crawlab。

## 技术栈

### 后端
- FastAPI - 现代、快速的 Web 框架
- SQLAlchemy + Alembic - ORM 和数据库迁移
- APScheduler - 任务调度
- WebSocket - 实时日志推送
- PostgreSQL - 生产数据库（开发使用 SQLite）

### 前端
- Vue 3 + TypeScript
- Vite
- Element Plus
- Vue Router
- Pinia

## 项目结构

```
crawlscheduler/
├── backend/           # FastAPI 后端
│   ├── app/
│   ├── alembic/
│   └── requirements.txt
├── frontend/          # Vue 3 前端
│   └── src/
└── data/             # 运行时数据
```

## 快速开始

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 查看前端界面。

API 文档: http://localhost:8000/docs

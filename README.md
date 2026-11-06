# 码智星 OJ 平台

面向少儿 Python/C++ 信奥编程教学的 Web 端 OJ 平台，支持教师作业管理、学生在线刷题、沙箱判题、AI 错题解析与家校学情可视化。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Pinia + Monaco Editor + Tailwind |
| 后端 | FastAPI + SQLAlchemy 2.0 + Alembic + JWT |
| 数据库 | MySQL 8（生产）/ SQLite（开发） |
| 判题 | Judge0 + Docker 沙箱 |
| 任务队列 | Celery + Redis |
| AI | OpenAI 兼容 API |

## 本地开发

### 1. 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

开发默认：SQLite、同步判题（Celery eager）、Mock 短信、自动 seed 演示数据。

### 2. 前端

```bash
npm install
npm run dev
```

访问 http://localhost:5173（或 Vite 提示的端口）。

### 3. 演示账号（seed 后）

| 角色 | 账号 | 密码 |
|------|------|------|
| 教师 | 13800138000 | Teacher123 |
| 学生 | stu2024001 | 123456 |
| 家长 | 13900139000 | Parent123 |

### 4. 可选：Judge0 沙箱（更接近生产）

```bash
./backend/scripts/start_judge0.sh
```

在 `backend/.env` 中设置：

```env
JUDGE0_URL=http://localhost:2358
JUDGE0_REQUIRED=false
JUDGE0_ALLOW_LOCAL_FALLBACK=true
```

### 5. 可选：Redis + Celery 异步判题

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

```env
CELERY_TASK_ALWAYS_EAGER=false
CELERY_BROKER_URL=redis://localhost:6379/0
```

另开终端：

```bash
cd backend && celery -A app.celery_app:celery_app worker --loglevel=info
# 排行榜日刷新（可选）
./backend/scripts/run_celery_beat.sh
```

## 生产部署（方案 A：一键自用）

### 步骤

1. **复制并编辑环境变量**

```bash
cp backend/.env.production.example backend/.env
# 编辑 SECRET_KEY、CORS_ORIGINS、OPENAI_API_KEY、短信配置等
python backend/scripts/check_production_env.py
```

2. **一键启动**

```bash
chmod +x deploy/scripts/prod-up.sh
./deploy/scripts/prod-up.sh
```

将启动：MySQL、Redis、Judge0、Backend、Celery Worker、Frontend（Nginx）。

3. **访问**

- 前端：http://localhost
- 后端健康检查：http://localhost:8000/health
- API：`/api/v1/*`

### 生产必填项

详见 [deploy/PRODUCTION_CHECKLIST.md](deploy/PRODUCTION_CHECKLIST.md)

| 变量 | 说明 |
|------|------|
| `DEBUG=false` | 开启生产校验 |
| `SECRET_KEY` | ≥32 位随机字符串 |
| `DATABASE_URL` | MySQL 连接串 |
| `CORS_ORIGINS` | 前端 HTTPS 域名 |
| `JUDGE0_URL` | Docker 内网 `http://judge0-server:2358` |
| `JUDGE0_ALLOW_LOCAL_FALLBACK=false` | 禁止宿主机 subprocess 判题 |
| `CELERY_TASK_ALWAYS_EAGER=false` | 异步判题 |
| `OPENAI_API_KEY` | AI 解析（`AI_ENABLED=true` 时） |
| `ENABLE_SEED=false` | 禁止写入演示数据 |

### HTTPS 与监控

```bash
# HTTPS
export DOMAIN=your-domain.com
./deploy/scripts/init-letsencrypt.sh
docker compose -f docker-compose.prod.yml -f docker-compose.https.yml up -d

# Prometheus + Grafana
docker compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d
```

## 测试

```bash
cd backend
pytest -v
```

覆盖：认证/单点登录、作业发布校验、通知公告权限。

## 目录结构

```
├── src/                 # Vue 3 前端
├── backend/             # FastAPI 后端
│   ├── app/             # 业务代码
│   ├── alembic/         # 数据库迁移
│   └── tests/           # pytest
├── deploy/              # 部署脚本与检查清单
├── docker-compose.prod.yml
└── docker-compose.judge0.yml  # 独立 Judge0（开发用）
```

## 核心功能

- 三角色权限（教师 / 学生 / 家长）
- 班级与学生管理、家长绑定
- 题库 CRUD、作业布置/撤回/补交
- Monaco 在线编辑、草稿缓存
- Judge0 沙箱判题（AC/WA/CE/TLE/RE）
- AI 错题解析（仅 WA/RE，50 次/日限流）
- 错题本、班级排行榜、学情分析
- **通知公告**（教师发布 → 学生/家长查看）
- **排行榜日快照**（Celery Beat 每日 00:00 北京时间刷新）
- **家长端四页**（学情总览 / 学习趋势 / 薄弱知识点 / 高频错题）
- **全场景埋点**（教师/学生/家长操作 + 页面停留 + 异常）

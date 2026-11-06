# 生产环境 .env 检查清单

## 一键部署

```bash
cp backend/.env.production.example backend/.env
# 编辑 backend/.env 后：
./deploy/scripts/prod-up.sh
```

`docker-compose.prod.yml` 已内置 MySQL、Redis、Judge0、Backend、Celery Worker、Frontend。

## 手动检查

部署前复制 `backend/.env.production.example` 为 `backend/.env`，逐项确认。

也可运行自动检查：

```bash
cd backend
python scripts/check_production_env.py
```

## 必填项（P0）

| 变量 | 要求 | 说明 |
|------|------|------|
| `DEBUG` | `false` | 开启生产校验、关闭 Swagger |
| `SECRET_KEY` | ≥32 位随机字符串 | `openssl rand -hex 32` 生成 |
| `DATABASE_URL` | `mysql+pymysql://...` | 禁止 SQLite |
| `CORS_ORIGINS` | `https://你的域名` | 与前端访问地址一致，不含 localhost |
| `JUDGE0_URL` | 可访问的 Judge0 地址 | 如 `http://judge0:2358`（Docker 内网） |
| `JUDGE0_ALLOW_LOCAL_FALLBACK` | `false` | 禁止宿主机 subprocess 判题 |
| `CELERY_TASK_ALWAYS_EAGER` | `false` | 异步判题必须走 Celery Worker |
| `CELERY_BROKER_URL` | Redis 地址 | 与 Worker 一致 |
| `ENABLE_SEED` | `false` | 禁止写入演示数据 |
| `ENABLE_OPENAPI` | `false` | 关闭 API 文档暴露 |

## 推荐项（P1）

| 变量 | 要求 | 说明 |
|------|------|------|
| `SMS_PROVIDER` | `aliyun` | 生产真实发短信 |
| `ALIYUN_SMS_*` | 全部填写 | 签名、模板、AccessKey |
| `METRICS_ENABLED` | `true` | 暴露 `/metrics` 供 Prometheus 采集 |
| `METRICS_TOKEN` | 随机字符串 | `Authorization: Bearer <token>` 保护指标端点 |
| `OPENAI_API_KEY` | 有效 Key | `AI_ENABLED=true` 时必填 |
| `JUDGE0_AUTH_TOKEN` | 若 Judge0 开启鉴权则填写 | |
| `MYSQL_PASSWORD` | 强密码 | docker-compose 与 DATABASE_URL 保持一致 |

## 短信（阿里云）

1. 控制台开通 [短信服务](https://dysmsapi.console.aliyun.com/)
2. 创建签名（如「码智星」）并审核通过
3. 创建验证码模板，变量名 `code`
4. 配置：

```env
SMS_ENABLED=true
SMS_PROVIDER=aliyun
ALIYUN_SMS_ACCESS_KEY_ID=LTAI...
ALIYUN_SMS_ACCESS_KEY_SECRET=...
ALIYUN_SMS_SIGN_NAME=你的短信签名
ALIYUN_SMS_TEMPLATE_CODE=SMS_xxxxxxxx
# 注册/重置可共用同一模板，也可分别指定：
# ALIYUN_SMS_TEMPLATE_CODE_REGISTER=SMS_xxx
# ALIYUN_SMS_TEMPLATE_CODE_RESET=SMS_yyy
```

## HTTPS

1. 域名 DNS 解析到服务器
2. 首次申请证书：

```bash
export DOMAIN=your-domain.com
export CERTBOT_EMAIL=admin@your-domain.com
./deploy/scripts/init-letsencrypt.sh
```

3. 使用 HTTPS compose 启动：

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.https.yml up -d
```

4. 确认 `CORS_ORIGINS=https://your-domain.com`

## 监控

启动 Prometheus + Grafana：

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d
```

- Prometheus: `http://服务器:9090`
- Grafana: `http://服务器:3001`（默认 admin/admin，首次登录修改）
- 后端指标: `GET /metrics`，Header: `Authorization: Bearer <METRICS_TOKEN>`

## 部署前冒烟测试

```bash
# 健康检查（应返回 status=ok）
curl -s https://your-domain.com/health | jq .

# 登录限流与短信（教师注册/登录）
curl -X POST https://your-domain.com/api/v1/auth/send-code ...

# 判题链路（学生提交后 status 应从 PENDING → AC/WA/...）
```

## 常见错误

| 现象 | 原因 |
|------|------|
| 启动报 `SECRET_KEY` | 未替换默认密钥 |
| 启动报 `SQLite` | DATABASE_URL 仍为 sqlite |
| 验证码收不到 | SMS 未配置或模板/签名未审核 |
| 提交一直 PENDING | Celery Worker 未启动或 Redis 不通 |
| 401 其他设备登录 | 单设备登录，旧 Token 已失效（正常） |

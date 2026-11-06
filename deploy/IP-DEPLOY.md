# 备案前：公网 IP + 8080 部署说明

适用于 **已买腾讯云轻量、域名备案未完成** 阶段。用户通过 `http://你的公网IP:8080` 访问，**不要** 将域名 A 记录指到服务器。

## 1. 轻量防火墙

| 端口 | 来源 | 说明 |
|------|------|------|
| 22 | 你的办公/家庭 IP | SSH |
| 8080 | 0.0.0.0/0 | Web（Nginx → 后端） |

**不要开放**：8000、3306、6379、2358。

`docker-compose.prod.yml` 已配置：**frontend 8080:80**，**backend 不映射宿主机 8000**（仅 Docker 内网 `backend:8000`）。

## 2. backend/.env（关键项）

```env
DEBUG=false
CORS_ORIGINS=http://你的公网IP:8080

ENABLE_SEED=false
ENABLE_OPENAPI=false

# 短信、SECRET_KEY、MySQL 等同生产清单
```

`python3 backend/scripts/check_production_env.py` 对 `http://` CORS 可能报 FAIL，**备案前可忽略**，以浏览器能登录为准。

## 3. 启动

```bash
export MYSQL_PASSWORD='强密码'
export MYSQL_ROOT_PASSWORD='另一强密码'
./deploy/scripts/prod-up.sh
```

脚本健康检查走 **`http://127.0.0.1:8080/health`**（经 Nginx 反代）。

## 4. 验证

- 浏览器：`http://公网IP:8080`
- 短信注册、提交判题各测一次
- 外网确认 **无法** 访问 `http://公网IP:8000`

## 5. 备案通过后

1. DNS A 记录 → 轻量 IP  
2. 防火墙增加 80、443  
3. `CORS_ORIGINS=https://你的域名`  
4. `./deploy/scripts/init-letsencrypt.sh` + `docker compose -f docker-compose.prod.yml -f docker-compose.https.yml up -d`  
5. 使用 `docker-compose.https.yml` 时会 **覆盖** frontend 端口为 `80:80`、`443:443`（不再使用 8080）；防火墙放行 80/443 后关闭 8080 即可

详见 [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)。

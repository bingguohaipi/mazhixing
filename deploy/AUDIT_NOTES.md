# 安全与资产审计说明

## 1. 漏洞扫描（本地）

```bash
chmod +x deploy/scripts/security_scan.sh
./deploy/scripts/security_scan.sh
```

- **pip-audit**：检查 `backend/requirements.txt` 已知 CVE。
- **bandit**：Python 静态安全问题（`backend/app`）。
- **npm audit**：需使用 `registry.npmjs.org`（若 `.npmrc` 为 npmmirror，audit 不可用）。

上线前另做：**防火墙仅 22/8080 或 443**、生产 `.env` 检查脚本、`ENABLE_OPENAPI=false`。

### 最近一次 pip-audit（requirements 锁定版本）

| 包 | 锁定版本 | 建议 |
|----|----------|------|
| python-multipart | 已升至 **0.0.33** | 修复多条 PYSEC-2026-* |
| starlette | **0.47.3**（requirements 显式 pin） | 已随 FastAPI **0.116.2** 升级 |
| pytest | 8.3.4 | 开发依赖，可升至 9.0.3 |
| ecdsa | 经 python-jose 引入 | 关注上游修复；JWT 使用 HS256 时实际风险较低 |

升级 FastAPI 后请执行：`cd backend && pytest`。

## 2. 字体商用

项目 **未打包** 自定义 `.woff/.ttf` 到 `src/`。界面使用 **系统字体栈**（见 `src/assets/styles/main.css`）：

- `-apple-system` / `BlinkMacSystemFont`：随 Apple 系统授权给终端用户显示。
- `PingFang SC`、`Microsoft YaHei` 等：依赖用户 OS 自带字体，**网站未嵌入分发**。
- 等宽栈中的 `Fira Code` 仅作 **fallback**（用户本机未安装则不会加载）；若将来 **自行托管** Fira Code，需遵循 [SIL Open Font License](https://github.com/tonsky/FiraCode)。
- **Monaco Editor / codicon**：npm 依赖内嵌，开发/构建产物；Monaco 为 MIT，codicon 随 VS Code 生态常用 MIT 许可（见 `node_modules/monaco-editor` 许可证）。

**结论**：当前实现方式可商用；避免在 CSS 中 `@font-face` 嵌入未授权字库文件。

## 3. 后端路由与前端

```bash
python3 deploy/scripts/compare_api_routes.py
```

「未匹配」不等于废弃：可能由 tracker、导出下载、Swagger 关闭后仍保留的管理 API 等使用。

## 4. 中文注释

核心安全与认证模块已补充中文 docstring；业务 service 层可按模块逐步补充。

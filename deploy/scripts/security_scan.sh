#!/usr/bin/env bash
# 本地安全扫描：Python 依赖 CVE + Bandit 静态检查 + 前端 npm audit（需官方 registry）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "==> Backend: pip-audit (requirements.txt)"
if ! python3 -m pip_audit -r backend/requirements.txt 2>/dev/null; then
  echo "    安装: python3 -m pip install pip-audit"
  echo "    若网络受限，请在可访问 PyPI 的环境运行本脚本"
fi

echo ""
echo "==> Backend: bandit (app/, 中高危)"
if ! python3 -m bandit -r backend/app -ll -q 2>/dev/null; then
  echo "    安装: python3 -m pip install bandit"
fi

echo ""
echo "==> Frontend: npm audit (需 registry.npmjs.org，非 npmmirror)"
(
  cd "$ROOT"
  npm audit --registry=https://registry.npmjs.org/ 2>/dev/null || echo "    npm audit 失败：检查 .npmrc 是否指向 npmmirror（不支持 audit）"
)

echo ""
echo "完成。结合 deploy/AUDIT_NOTES.md 与上线防火墙清单。"

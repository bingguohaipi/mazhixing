# 一期 P0 回归验收清单（PRD 9.2）

执行人：________　日期：________　环境：□ 本地 □ 生产

## 权限与越权

- [ ] 未登录访问 `/teacher/questions` 跳转登录
- [ ] 学生访问 `/teacher/analytics` 进入 `/403`，文案「暂无权限访问该页面」
- [ ] 家长仅可查看绑定子女学情（换 student_id 应 403）

## 空状态

- [ ] 学生无作业：工作台「暂无作业，请等待老师布置」
- [ ] 学生无错题：错题本「太棒了，暂无错题」
- [ ] 教师无班级：班级列表空状态 + 引导创建

## 网络与提交

- [ ] 做题页断网提交：提示「提交失败，已为你保存草稿，网络恢复后可重新提交」+ 可重试
- [ ] 判题 PENDING 中断网：轮询恢复后仍拿到最终状态
- [ ] 空代码 / 危险系统调用：前后端均拦截

## 判题与 AI

- [ ] WA/RE 可触发 AI，CE 不触发
- [ ] AI 超限：「今日 AI 解析次数已达上限，请明日再来」
- [ ] AI 失败：「解析暂时失败，请稍后刷新重试」；编辑器行号高亮生效

## 埋点（管理后台 → 埋点概览）

- [ ] `code_submit` / `code_submit_fail` 有记录
- [ ] `forbidden_access` 越权有记录
- [ ] `ai_analysis_fail` 失败有记录

## 性能（参考）

- [ ] `GET /health` < 300ms（本地：`python backend/scripts/perf_health_check.py`）
- [ ] 生产可选：`docker compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d`

## 自动化

- [ ] `cd backend && pytest`
- [ ] `npm run test:unit`
- [ ] `npm run test:e2e`

# Issue Triage Agent

GitHub Issue 智能分诊 Agent — 自动分类、打标签、找相似 Issue、推荐处理人。

## 架构

```
GitHub Webhook / 轮询
        │
        ▼
┌─────────────────────┐
│   Triage Orchestrator│
└──┬──────┬──────┬────┘
   │      │      │
   ▼      ▼      ▼
┌──────┐┌──────┐┌──────┐
│Agent1││Agent2││Agent3│
│分类   ││相似度 ││分配   │
└──┬───┘└──┬───┘└──┬───┘
   │      │      │
   └──────┴──────┘
        │
        ▼
  打标签 + 评论 + 分配
```

## 多 Agent 协作

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| 分类 Agent | 判断类型、优先级、模块 | Issue 内容 + 仓库标签列表 | category, priority, module, labels |
| 相似度 Agent | 匹配历史 Issue | Issue 内容 + 历史 Issue 列表 | 相似 Issue 列表 + 相似度分数 |
| 分配 Agent | 推荐处理人 | 分类结果 + 贡献者列表 | 推荐 assignee + 理由 |

三个 Agent 并行执行，结果汇总到 Orchestrator 生成分诊报告。

## 使用

### 环境变量

```bash
export GITHUB_TOKEN="your_github_pat"
export XIAOMI_API_KEY="your_api_key"
export XIAOMI_BASE_URL="https://token-plan-cn.xiaomimimo.com/v1"
```

### 单次分诊（试运行）

```bash
python run.py owner/repo --dry
```

### 单次分诊（实际执行）

```bash
python run.py owner/repo 42    # 分诊指定 Issue
python run.py owner/repo       # 分诊所有未分诊的 open Issue
```

### Webhook 模式（实时响应）

```bash
python webhook_server.py
# 监听 0.0.0.0:9876
# 在 GitHub 仓库 Settings → Webhooks 添加:
#   URL: http://<your-ip>:9876/webhook
#   Content type: application/json
#   Events: Issues
```

### 配置项（config.py）

| 配置 | 默认值 | 说明 |
|------|--------|------|
| AUTO_COMMENT | True | 自动添加分诊评论 |
| AUTO_LABEL | True | 自动打标签 |
| AUTO_ASSIGN | True | 自动分配处理人 |
| DRY_RUN | False | 试运行模式 |
| MAX_HISTORY_ISSUES | 50 | 检索历史 Issue 数量 |

## 项目结构

```
issue-triage-agent/
├── config.py           # 配置
├── github_client.py    # GitHub API 封装
├── analyzer.py         # 多 Agent LLM 分析（分类/相似度/分配）
├── triage.py           # 分诊编排逻辑
├── webhook_server.py   # Webhook 服务器
├── run.py              # 命令行入口
└── README.md
```

## 依赖

- Python 3.11+
- requests
- openai

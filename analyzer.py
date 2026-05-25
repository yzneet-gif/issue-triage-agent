"""LLM Analyzer - Multi-agent Issue Analysis"""
import json
from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)


def _call_llm(system: str, user: str, temperature: float = 0.3) -> str:
    """调用 LLM"""
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=2048,
    )
    return resp.choices[0].message.content.strip()


def _parse_json(text: str):
    """从 LLM 回复中提取 JSON"""
    import re
    # 尝试直接解析
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 提取 ```json ... ``` 块
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # 提取第一个 { ... } 或 [ ... ]
    for pattern in [r"\{.*\}", r"\[.*\]"]:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return None


def classify_issue(issue: dict, labels: list[str]) -> dict:
    """分类 Agent - 判断 Issue 类型、模块、优先级"""
    system = """你是一个 Issue 分类专家。根据 Issue 内容，返回 JSON：
{"category": "bug|feature|question|docs|performance|security|refactor", "priority": "critical|high|medium|low", "module": "涉及的模块/组件名", "suggested_labels": ["从给定标签列表中选择合适的标签"], "confidence": 0.0-1.0, "reasoning": "简要推理过程"}
只返回 JSON，不要其他内容。"""

    user = f"""可用标签: {json.dumps(labels, ensure_ascii=False)}

Issue #{issue['number']}: {issue['title']}
---
{issue.get('body', '(无描述)')[:3000]}"""

    result = _call_llm(system, user)
    parsed = _parse_json(result)
    if parsed and isinstance(parsed, dict):
        return parsed
    return {
        "category": "unknown", "priority": "medium", "module": "unknown",
        "suggested_labels": [], "confidence": 0.0,
        "reasoning": f"解析失败: {result[:200]}"
    }


def find_similar_issues(issue: dict, history_issues: list[dict]) -> list[dict]:
    """相似度 Agent - 从历史 Issue 中找相似的"""
    if not history_issues:
        return []

    history_text = "\n".join(
        f"- #{i['number']}: {i['title']} [{','.join(l['name'] for l in i.get('labels', []))}]"
        for i in history_issues[:30]
    )

    system = """你是一个 Issue 相似度分析专家。从历史 Issue 列表中找出与当前 Issue 最相似的（最多 5 个）。
返回 JSON 数组：
[{"number": 123, "similarity": 0.85, "reason": "相似原因"}]
只返回 JSON，不要其他内容。"""

    user = f"""当前 Issue #{issue['number']}: {issue['title']}
{issue.get('body', '')[:2000]}

历史 Issue 列表:
{history_text}"""

    result = _call_llm(system, user)
    parsed = _parse_json(result)
    if parsed and isinstance(parsed, list):
        return parsed
    return []


def suggest_assignee(issue: dict, classification: dict, contributors: list[dict]) -> dict:
    """分配 Agent - 推荐处理人"""
    if not contributors:
        return {"assignee": None, "reason": "无可用贡献者"}

    contrib_names = [c["login"] for c in contributors[:15]]

    system = f"""你是一个任务分配专家。根据 Issue 的分类和模块，从贡献者列表中推荐最合适的处理人。
返回 JSON：
{{"assignee": "推荐的用户名", "reason": "推荐理由", "backup": "备选用户名"}}

如果无法判断，assignee 设为 null。只返回 JSON。"""

    user = f"""Issue #{issue['number']}: {issue['title']}
分类: {classification.get('category', 'unknown')}
模块: {classification.get('module', 'unknown')}
优先级: {classification.get('priority', 'medium')}

可用贡献者: {', '.join(contrib_names)}"""

    result = _call_llm(system, user)
    parsed = _parse_json(result)
    if parsed and isinstance(parsed, dict):
        return parsed
    return {"assignee": None, "reason": f"解析失败: {result[:200]}"}


def generate_triage_comment(classification: dict, similar: list, assignment: dict) -> str:
    """生成分诊摘要评论"""
    lines = ["## 🤖 AI Triage Report\n"]

    # 分类
    cat = classification.get("category", "unknown")
    pri = classification.get("priority", "medium")
    conf = classification.get("confidence", 0)
    emoji_map = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
    lines.append(f"**类型**: `{cat}` | **优先级**: {emoji_map.get(pri, '⚪')} `{pri}` | **置信度**: `{conf:.0%}`")
    lines.append(f"**模块**: `{classification.get('module', 'unknown')}`")
    if classification.get("reasoning"):
        lines.append(f"**推理**: {classification['reasoning']}")
    lines.append("")

    # 相似 Issue
    if similar:
        lines.append("**🔗 相似历史 Issue:**")
        for s in similar[:3]:
            lines.append(f"- #{s['number']} (相似度 {s.get('similarity', '?')}) — {s.get('reason', '')}")
        lines.append("")

    # 分配建议
    if assignment.get("assignee"):
        lines.append(f"**👤 建议处理人**: @{assignment['assignee']} — {assignment.get('reason', '')}")
        if assignment.get("backup"):
            lines.append(f"**备选**: @{assignment['backup']}")
    lines.append("")

    lines.append("---")
    lines.append("*由 Issue Triage Agent 自动生成*")
    return "\n".join(lines)

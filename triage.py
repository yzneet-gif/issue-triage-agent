"""Triage Orchestrator - 主调度逻辑"""
import json
import time
from github_client import GitHubClient
from analyzer import classify_issue, find_similar_issues, suggest_assignee, generate_triage_comment
from config import AUTO_COMMENT, AUTO_LABEL, AUTO_ASSIGN, MAX_HISTORY_ISSUES
import config as app_config


def triage_issue(gh: GitHubClient, owner: str, repo: str, issue_number: int) -> dict:
    """对单个 Issue 执行完整分诊流程"""
    print(f"\n{'='*60}")
    print(f"🔍 开始分诊 Issue #{issue_number}")
    print(f"{'='*60}")

    # 1. 获取 Issue 详情
    issue = gh.get_issue(owner, repo, issue_number)
    print(f"📋 标题: {issue['title']}")
    print(f"   状态: {issue['state']} | 创建: {issue['created_at'][:10]}")

    # 2. 获取仓库标签列表
    labels_data = gh.get_labels(owner, repo)
    label_names = [l["name"] for l in labels_data]
    print(f"🏷️  仓库标签: {len(label_names)} 个")

    # 3. 获取历史 Issue（用于相似度匹配）
    history = gh.get_issues(owner, repo, state="all", per_page=MAX_HISTORY_ISSUES)
    print(f"📚 历史 Issue: {len(history)} 条")

    # 4. 获取贡献者
    contributors = gh.get_contributors(owner, repo)
    print(f"👥 贡献者: {len(contributors)} 人")

    # === 多 Agent 并行分析 ===
    print(f"\n🤖 启动多 Agent 分析...")

    # Agent 1: 分类
    print("   ├─ [Agent 1] 分类中...")
    t0 = time.time()
    classification = classify_issue(issue, label_names)
    print(f"   │  分类: {classification.get('category')} | 优先级: {classification.get('priority')} ({time.time()-t0:.1f}s)")

    # Agent 2: 相似度匹配
    print("   ├─ [Agent 2] 查找相似 Issue...")
    t0 = time.time()
    similar = find_similar_issues(issue, history)
    print(f"   │  找到 {len(similar)} 个相似 Issue ({time.time()-t0:.1f}s)")

    # Agent 3: 分配推荐
    print("   └─ [Agent 3] 推荐处理人...")
    t0 = time.time()
    assignment = suggest_assignee(issue, classification, contributors)
    print(f"   │  推荐: {assignment.get('assignee', '无')} ({time.time()-t0:.1f}s)")

    # 5. 生成报告
    comment = generate_triage_comment(classification, similar, assignment)
    print(f"\n📝 分诊报告已生成")

    result = {
        "issue_number": issue_number,
        "title": issue["title"],
        "classification": classification,
        "similar_issues": similar,
        "assignment": assignment,
        "comment": comment,
        "actions_taken": [],
    }

    # 6. 执行操作
    if app_config.DRY_RUN:
        print("\n⚠️  DRY RUN 模式 — 不执行实际操作")
        print(f"\n--- 预览评论 ---\n{comment}\n--- END ---")
        result["actions_taken"].append("dry_run")
    else:
        # 打标签
        if AUTO_LABEL and classification.get("suggested_labels"):
            labels_to_add = [l for l in classification["suggested_labels"] if l in label_names]
            if labels_to_add:
                gh.add_labels(owner, repo, issue_number, labels_to_add)
                print(f"✅ 已添加标签: {labels_to_add}")
                result["actions_taken"].append(f"labels:{','.join(labels_to_add)}")

        # 添加评论
        if AUTO_COMMENT:
            gh.add_comment(owner, repo, issue_number, comment)
            print(f"✅ 已添加分诊评论")
            result["actions_taken"].append("comment")

        # 分配
        if AUTO_ASSIGN and assignment.get("assignee"):
            try:
                gh.assign_issue(owner, repo, issue_number, [assignment["assignee"]])
                print(f"✅ 已分配给: @{assignment['assignee']}")
                result["actions_taken"].append(f"assign:{assignment['assignee']}")
            except Exception as e:
                print(f"⚠️  分配失败: {e}")
                result["actions_taken"].append(f"assign_failed:{e}")

    print(f"\n✨ Issue #{issue_number} 分诊完成")
    return result


def triage_new_issues(gh: GitHubClient, owner: str, repo: str, since_minutes: int = 30) -> list[dict]:
    """分诊最近新建的 Issue"""
    issues = gh.get_issues(owner, repo, state="open")
    results = []

    for issue in issues:
        # 简单判断：如果已经有 AI 分诊评论就跳过
        comments = gh.get_issue_comments(owner, repo, issue["number"])
        already_triaged = any("AI Triage Report" in c.get("body", "") for c in comments)
        if already_triaged:
            print(f"⏭️  Issue #{issue['number']} 已分诊，跳过")
            continue

        result = triage_issue(gh, owner, repo, issue["number"])
        results.append(result)
        time.sleep(1)  # 避免 API 限流

    return results

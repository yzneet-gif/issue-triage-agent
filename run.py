"""One-shot triage - 手动测试用"""
import sys
from github_client import GitHubClient
from triage import triage_issue, triage_new_issues
import config


def main():
    gh = GitHubClient()

    if len(sys.argv) < 2:
        print("用法:")
        print("  python run.py <owner/repo>              # 分诊所有未分诊的 open Issue")
        print("  python run.py <owner/repo> <number>      # 分诊指定 Issue")
        print("  python run.py <owner/repo> --dry         # 试运行（不实际修改）")
        print()
        print("示例:")
        print("  python run.py NousResearch/hermes-agent")
        print("  python run.py NousResearch/hermes-agent 42")
        print("  python run.py NousResearch/hermes-agent --dry")
        return

    repo_path = sys.argv[1]
    owner, repo = repo_path.split("/")

    if "--dry" in sys.argv:
        config.DRY_RUN = True
        print("⚠️  DRY RUN 模式开启\n")

    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        # 分诊单个 Issue
        issue_number = int(sys.argv[2])
        result = triage_issue(gh, owner, repo, issue_number)
        print(f"\n{'='*60}")
        print(f"结果: {result['actions_taken']}")
    else:
        # 分诊所有未分诊的
        results = triage_new_issues(gh, owner, repo)
        print(f"\n{'='*60}")
        print(f"共分诊 {len(results)} 个 Issue")
        for r in results:
            print(f"  #{r['issue_number']}: {r['classification'].get('category')} | {r['actions_taken']}")


if __name__ == "__main__":
    main()

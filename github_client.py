"""GitHub API Client"""
import requests
import json
from config import GITHUB_TOKEN, GITHUB_API


class GitHubClient:
    def __init__(self, token: str = GITHUB_TOKEN):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def get_issues(self, owner: str, repo: str, state: str = "open", per_page: int = 50, since: str = None) -> list:
        """获取仓库 Issue 列表"""
        params = {"state": state, "per_page": per_page, "sort": "created", "direction": "desc"}
        if since:
            params["since"] = since
        resp = self.session.get(f"{GITHUB_API}/repos/{owner}/{repo}/issues", params=params)
        resp.raise_for_status()
        # 过滤掉 PR（GitHub API 把 PR 也算 Issue）
        return [i for i in resp.json() if "pull_request" not in i]

    def get_issue(self, owner: str, repo: str, issue_number: int) -> dict:
        """获取单个 Issue 详情"""
        resp = self.session.get(f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}")
        resp.raise_for_status()
        return resp.json()

    def get_issue_comments(self, owner: str, repo: str, issue_number: int) -> list:
        """获取 Issue 评论"""
        resp = self.session.get(f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/comments")
        resp.raise_for_status()
        return resp.json()

    def get_labels(self, owner: str, repo: str) -> list:
        """获取仓库所有标签"""
        resp = self.session.get(f"{GITHUB_API}/repos/{owner}/{repo}/labels", params={"per_page": 100})
        resp.raise_for_status()
        return resp.json()

    def add_labels(self, owner: str, repo: str, issue_number: int, labels: list) -> dict:
        """给 Issue 添加标签"""
        resp = self.session.post(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/labels",
            json={"labels": labels}
        )
        resp.raise_for_status()
        return resp.json()

    def add_comment(self, owner: str, repo: str, issue_number: int, body: str) -> dict:
        """给 Issue 添加评论"""
        resp = self.session.post(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/comments",
            json={"body": body}
        )
        resp.raise_for_status()
        return resp.json()

    def assign_issue(self, owner: str, repo: str, issue_number: int, assignees: list) -> dict:
        """分配 Issue"""
        resp = self.session.post(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/assignees",
            json={"assignees": assignees}
        )
        resp.raise_for_status()
        return resp.json()

    def get_contributors(self, owner: str, repo: str) -> list:
        """获取仓库贡献者列表"""
        resp = self.session.get(f"{GITHUB_API}/repos/{owner}/{repo}/contributors", params={"per_page": 30})
        resp.raise_for_status()
        return resp.json()

    def get_repo_languages(self, owner: str, repo: str) -> dict:
        """获取仓库语言分布"""
        resp = self.session.get(f"{GITHUB_API}/repos/{owner}/{repo}/languages")
        resp.raise_for_status()
        return resp.json()

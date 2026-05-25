"""Webhook Server - 接收 GitHub Webhook 触发自动分诊"""
import json
import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from github_client import GitHubClient
from triage import triage_issue
import config


class WebhookHandler(BaseHTTPRequestHandler):
    gh = None  # 类级别共享

    def do_POST(self):
        # 读取请求体
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # 验证签名（可选）
        secret = getattr(config, "WEBHOOK_SECRET", "")
        if secret:
            sig = self.headers.get("X-Hub-Signature-256", "")
            expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Invalid signature")
                return

        # 解析事件
        event = self.headers.get("X-GitHub-Event", "")
        payload = json.loads(body)

        if event == "issues" and payload.get("action") == "opened":
            issue = payload["issue"]
            repo = payload["repository"]
            owner = repo["owner"]["login"]
            repo_name = repo["name"]
            issue_number = issue["number"]

            print(f"\n🔔 收到新 Issue: #{issue_number} - {issue['title']}")
            try:
                result = triage_issue(self.gh, owner, repo, issue_number)
                print(f"✅ 分诊完成，操作: {result['actions_taken']}")
            except Exception as e:
                print(f"❌ 分诊失败: {e}")

            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ignored", "event": event}).encode())

    def log_message(self, format, *args):
        print(f"[Webhook] {args[0]}")


def run_server(host: str = "0.0.0.0", port: int = 9876):
    """启动 Webhook 服务器"""
    WebhookHandler.gh = GitHubClient()
    server = HTTPServer((host, port), WebhookHandler)
    print(f"🚀 Issue Triage Agent 启动")
    print(f"   监听: http://{host}:{port}/webhook")
    print(f"   GitHub Webhook URL: http://<your-ip>:{port}/webhook")
    print(f"   Content-Type: application/json")
    print(f"   Events: Issues")
    print(f"   DRY_RUN: {config.DRY_RUN}")
    print(f"\n等待 Issue 事件中...")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
        server.server_close()


if __name__ == "__main__":
    run_server()

"""Issue Triage Agent - Configuration"""
import os

# GitHub
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_API = "https://api.github.com"

# LLM - Xiaomi MiMo
LLM_API_KEY = os.environ.get("XIAOMI_API_KEY", "")
LLM_BASE_URL = os.environ.get("XIAOMI_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "mimo-v2.5-pro")

# Triage settings
MAX_HISTORY_ISSUES = 50       # 检索历史 Issue 数量
SIMILARITY_THRESHOLD = 0.7    # 相似度阈值
AUTO_COMMENT = True           # 自动评论
AUTO_LABEL = True             # 自动打标签
AUTO_ASSIGN = True            # 自动分配
DRY_RUN = False               # 试运行（不实际修改 Issue）

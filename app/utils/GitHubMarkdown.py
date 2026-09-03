from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, unquote

import requests
from fastapi import HTTPException

_GITHUB_BLOB = re.compile(
    r"^https?://(?:www\.)?github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$",
    re.IGNORECASE,
)
_GITHUB_REPO = re.compile(
    r"^https?://(?:www\.)?github\.com/([^/]+)/([^/#?]+)/?$",
    re.IGNORECASE,
)
_RAW_HOSTS = {"raw.githubusercontent.com"}
_GITHUB_HOSTS = {"github.com", "www.github.com"}


def to_github_raw_url(url: str) -> str | None:
    """把 GitHub blob / 仓库地址转成 raw.githubusercontent.com。"""
    text = unquote((url or "").strip())
    if not text:
        return None

    parsed = urlparse(text)
    host = (parsed.hostname or "").lower()

    if host in _RAW_HOSTS and parsed.path.strip("/"):
        return f"https://raw.githubusercontent.com{parsed.path}"

    if host not in _GITHUB_HOSTS:
        return None

    blob = _GITHUB_BLOB.match(text.split("?", 1)[0].split("#", 1)[0])
    if blob:
        owner, repo, branch, path = blob.groups()
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"

    repo_match = _GITHUB_REPO.match(text.split("?", 1)[0].split("#", 1)[0])
    if repo_match:
        owner, repo = repo_match.groups()
        return f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"

    return None


def _raw_dir(raw_url: str) -> str:
    return raw_url.rsplit("/", 1)[0] + "/"


_MD_ASSET = re.compile(
    r"""(\[[^\]]*\]\()(?!https?:|/|#)([^)\s]+)(\))"""
)


def rewrite_relative_assets(markdown: str, raw_url: str) -> str:
    """把 README 里的相对图片/链接改成 raw GitHub 绝对地址。"""
    base = _raw_dir(raw_url)

    def repl(match: re.Match[str]) -> str:
        prefix, rel, suffix = match.groups()
        return f"{prefix}{urljoin(base, rel)}{suffix}"

    return _MD_ASSET.sub(repl, markdown)


def fetch_github_markdown(url: str) -> tuple[str, str]:
    """拉取 GitHub Markdown。返回 (markdown, raw_url)。"""
    raw_url = to_github_raw_url(url)
    if not raw_url:
        raise HTTPException(
            status_code=400,
            detail="仅支持 GitHub blob / raw / 仓库地址",
        )

    try:
        response = requests.get(
            raw_url,
            timeout=10,
            headers={"User-Agent": "kiri-blog-backend", "Accept": "text/plain"},
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="无法读取 GitHub 文档") from exc

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="作者未设置 README 文档")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="无法读取 GitHub 文档")

    markdown = rewrite_relative_assets(response.text, raw_url)
    return markdown, raw_url

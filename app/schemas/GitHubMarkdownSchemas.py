from pydantic import BaseModel


class GitHubMarkdownResponse(BaseModel):
    """GitHub Markdown 拉取结果。"""

    markdown: str
    source: str

from fastapi import APIRouter, Query

from app.common.Result import Result
from app.schemas.GitHubMarkdownSchemas import GitHubMarkdownResponse
from app.utils.GitHubMarkdown import fetch_github_markdown


router = APIRouter(prefix="/api/github", tags=["GitHub 文档"])


@router.get("/markdown", response_model=Result[GitHubMarkdownResponse])
def get_github_markdown(
    url: str = Query(..., description="GitHub blob / raw / 仓库地址"),
):
    """公开接口。把 GitHub Markdown 转成正文，供前台项目详情挂载。"""
    markdown, source = fetch_github_markdown(url)
    return Result.success(GitHubMarkdownResponse(markdown=markdown, source=source))

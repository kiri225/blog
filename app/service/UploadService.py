import uuid
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.Config import UPLOADS_DIR
from app.common.Result import Result
from app.schemas.UploadSchemas import UploadImageResponse

_ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/svg+xml",
}
_CONTENT_TYPE_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}
_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
_MAX_SIZE = 10 * 1024 * 1024


def upload_image(file: UploadFile) -> Result:
    """校验类型与大小后写入 uploads/，返回 url 与方向。

    Args:
        file: 上传的图片文件。

    Returns:
        统一结果集。成功时 code=200，data 含 url、orientation。
    """
    # 1.校验 Content-Type
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400, detail=f"不支持的文件类型: {content_type}"
        )

    # 2.读内容并校验大小
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = file.file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > _MAX_SIZE:
            raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
        chunks.append(chunk)
    content = b"".join(chunks)

    # 3.用 Pillow 读宽高判断方向；失败默认 landscape
    orientation = "landscape"
    try:
        with Image.open(BytesIO(content)) as img:
            width, height = img.size
            orientation = "landscape" if width >= height else "portrait"
    except (UnidentifiedImageError, OSError, ValueError):
        orientation = "landscape"

    # 4.写入 uploads/{uuid}{原扩展名}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_EXT:
        suffix = _CONTENT_TYPE_EXT[content_type]
    filename = f"{uuid.uuid4().hex}{suffix}"
    UPLOADS_DIR.mkdir(exist_ok=True)
    (UPLOADS_DIR / filename).write_bytes(content)

    # 5.统一结果集返回（相对路径；前台 / 管理端各自代理 /uploads）
    return Result.success(
        UploadImageResponse(url=f"/uploads/{filename}", orientation=orientation)
    )

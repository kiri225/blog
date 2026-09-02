from fastapi import Depends, File, UploadFile
from fastapi.routing import APIRouter

from app.Deps import get_current_user
from app.common.Result import Result
from app.schemas.UploadSchemas import UploadImageResponse
from app.service import UploadService as upload_service


router = APIRouter(prefix="/api/upload", tags=["上传"])


@router.post("/image", response_model=Result[UploadImageResponse])
def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """上传图片。

    需管理员 JWT。multipart 字段名 file。允许 jpeg / png / webp / gif / svg+xml，最大 10MB。
    学习阶段写入 uploads/，返回 /uploads/{filename}。

    Args:
        file: 上传的图片文件。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 含 url、orientation。
    """
    return upload_service.upload_image(file)

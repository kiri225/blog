from pydantic import BaseModel


class UploadImageResponse(BaseModel):
    """图片上传响应体。"""

    # 可访问的图片地址；本地模式为 /uploads/{filename}（前台/管理端代理到后端）
    url: str
    # 方向：宽 >= 高为 landscape，否则 portrait；读尺寸失败默认 landscape
    orientation: str

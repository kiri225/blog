from __future__ import annotations

from typing import Any, Generic, TypeVar
from pydantic import BaseModel

# data 的类型，如 Result[LoginResponse]
T = TypeVar("T")  

class Result(BaseModel, Generic[T]):
    """统一响应：业务状态码 + 说明 + 数据。code=0 表示成功。"""

    code: int = 200  # 业务状态码
    message: str = "success"  # 说明
    data: T | None = None  # 业务数据，无则 None

    @staticmethod
    def success(data: Any = None, message: str = "success") -> Result[Any]:
        """构造成功响应。

        Args:
            data: 业务数据，无则 None。
            message: 说明，默认 success。

        Returns:
            成功的 Result。
        """
        return Result(code=200, message=message, data=data)

    @staticmethod
    def fail(code: int, message: str, data: Any = None) -> Result[Any]:
        """构造失败响应。由全局异常拦截器调用，业务层不要直接 return。

        Args:
            code: 业务/HTTP 状态码。
            message: 失败说明。
            data: 附加数据，无则 None。

        Returns:
            失败的 Result。
        """
        return Result(code=code, message=message, data=data)

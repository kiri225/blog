from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.Result import Result


def register_exception_handlers(app: FastAPI) -> None:
    """把 HTTP / 校验 / 未捕获异常统一成 {code, message, data}。"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, str):
            message, data = detail, None
        else:
            message, data = "请求失败", detail
        return JSONResponse(
            status_code=exc.status_code,
            content=Result.fail(exc.status_code, message, data).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=Result.fail(422, "参数校验失败", exc.errors()).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=Result.fail(500, "服务器内部错误").model_dump(),
        )

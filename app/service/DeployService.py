import os
import subprocess
import threading

from app.common.Result import Result

_lock = threading.Lock()
_running = False

DEPLOY_ENABLED = os.getenv("DEPLOY_ENABLED", "") == "1"
DEPLOY_STACK_DIR = os.getenv("DEPLOY_STACK_DIR", "/stack")
DEPLOY_AGENT = os.getenv("DEPLOY_AGENT_CONTAINER", "blog-deploy-agent")


def _run_deploy() -> None:
    global _running
    try:
        subprocess.run(
            [
                "/usr/local/bin/docker",
                "exec",
                DEPLOY_AGENT,
                "sh",
                f"{DEPLOY_STACK_DIR}/deploy.sh",
            ],
            cwd=DEPLOY_STACK_DIR,
            timeout=3600,
            check=False,
        )
    finally:
        with _lock:
            _running = False


def trigger_deploy() -> Result:
    global _running

    if not DEPLOY_ENABLED:
        return Result.fail(403, "部署功能未启用")

    with _lock:
        if _running:
            return Result.fail(409, "已有部署任务正在执行，请稍后再试")
        _running = True

    threading.Thread(target=_run_deploy, daemon=True).start()
    return Result.success(
        {"status": "started"},
        message="已开始拉取最新代码并更新前台、后台、后端容器",
    )


def get_deploy_status() -> Result:
    with _lock:
        return Result.success({"running": _running})

# 一键启动联调：FastAPI + Next.js 博客前台 + Vue 管理后台
# 用法：在仓库根目录执行  .\dev.ps1

$ErrorActionPreference = "Stop"

$Backend = $PSScriptRoot
$Front = "D:\code-py\Fast-api\blog\front"
$Web = Join-Path $Front "web"
$Admin = Join-Path $Front "admin"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

function Ensure-Junction($link, $target) {
    if (Test-Path $link) { return }
    New-Item -ItemType Directory -Force -Path (Split-Path $link) | Out-Null
    New-Item -ItemType Junction -Path $link -Target $target | Out-Null
}

Ensure-Junction $Web "D:\code-py\Fast-api\blog\Kirameku\Kirameku"
Ensure-Junction $Admin "D:\code-py\Fast-api\blog\Kirameku\Kirameku-backend\admin"

if (-not (Test-Path $Python)) {
    Write-Host "找不到虚拟环境：$Python"
    Write-Host "请先：python -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt"
    exit 1
}

if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Host "找不到 pnpm，请先安装：npm install -g pnpm"
    exit 1
}

$pnpmInstall = @(
    "install",
    "--registry", "https://registry.npmmirror.com",
    "--fetch-timeout", "300000",
    "--config.dangerouslyAllowAllBuilds=true"
)

if (-not (Test-Path (Join-Path $Web "node_modules"))) {
    Write-Host "安装博客前台依赖（Next.js）..."
    Push-Location $Web
    pnpm @pnpmInstall
    Pop-Location
}

if (-not (Test-Path (Join-Path $Admin "node_modules"))) {
    Write-Host "安装管理后台依赖（Vue）..."
    $env:HUSKY = "0"
    Push-Location $Admin
    pnpm @pnpmInstall
    Pop-Location
}

Write-Host ""
Write-Host "启动三个窗口："
Write-Host "  后端 API     http://127.0.0.1:8000/docs"
Write-Host "  博客前台     http://localhost:3000"
Write-Host "  管理后台     http://localhost:8848"
Write-Host ""

$backendCmd = "Set-Location '$Backend'; & '$Python' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
$webCmd = "Set-Location '$Web'; pnpm dev"
$adminCmd = "Set-Location '$Admin'; `$env:HUSKY='0'; pnpm dev"

Start-Process powershell -ArgumentList @("-NoExit", "-Command", $backendCmd)
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList @("-NoExit", "-Command", $webCmd)
Start-Process powershell -ArgumentList @("-NoExit", "-Command", $adminCmd)

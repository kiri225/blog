#!/usr/bin/env bash
set -euo pipefail

# 在 home-debian 等 Linux 服务器上执行：
#   bash deploy.sh
#
# 首次部署前：
#   cp .env.example .env && vim .env

DEPLOY_DIR="${DEPLOY_DIR:-$(cd "$(dirname "$0")" && pwd)}"
REPOS_DIR="${REPOS_DIR:-$DEPLOY_DIR/repos}"

BLOG_REPO="${BLOG_REPO:-git@github.com:kiri225/blog.git}"
FRONTEND_REPO="${FRONTEND_REPO:-git@github.com:kiri225/Kirameku.git}"
ADMIN_REPO="${ADMIN_REPO:-git@github.com:kiri225/admin-blog.git}"

clone_or_pull() {
  local name="$1"
  local url="$2"
  local dir="$REPOS_DIR/$name"

  if [[ -d "$dir/.git" ]]; then
    echo ">>> 更新 $name"
    git -C "$dir" fetch origin
    git -C "$dir" checkout main
    git -C "$dir" pull --ff-only origin main
  else
    echo ">>> 克隆 $name"
    mkdir -p "$REPOS_DIR"
    git clone --branch main --depth 1 "$url" "$dir"
  fi
}

if [[ ! -f "$DEPLOY_DIR/.env" ]]; then
  echo "缺少 $DEPLOY_DIR/.env，请先复制 .env.example 并填写配置"
  exit 1
fi

clone_or_pull blog "$BLOG_REPO"
clone_or_pull Kirameku "$FRONTEND_REPO"
clone_or_pull admin "$ADMIN_REPO"

cp "$REPOS_DIR/blog/deploy/docker-compose.yml" "$DEPLOY_DIR/docker-compose.yml"
cp "$REPOS_DIR/blog/deploy/nginx.conf" "$DEPLOY_DIR/nginx.conf"
if [[ ! -f "$DEPLOY_DIR/.env.example" ]]; then
  cp "$REPOS_DIR/blog/deploy/.env.example" "$DEPLOY_DIR/.env.example"
fi

cd "$DEPLOY_DIR"

echo ">>> 构建并启动容器"
docker compose up -d --build --remove-orphans

echo ">>> 部署完成"
docker compose ps

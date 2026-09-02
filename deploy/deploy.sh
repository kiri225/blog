#!/usr/bin/env bash
set -euo pipefail

# 在服务器 /opt/blog-stack 执行：bash deploy.sh
# 也可由管理后台「更新部署」触发

DEPLOY_DIR="${DEPLOY_DIR:-$(cd "$(dirname "$0")" && pwd)}"
REPOS_DIR="${REPOS_DIR:-$DEPLOY_DIR/repos}"
LOG_FILE="${DEPLOY_DIR}/deploy.log"

BLOG_REPO="${BLOG_REPO:-git@github.com:kiri225/blog.git}"
FRONTEND_REPO="${FRONTEND_REPO:-git@github.com:kiri225/Kirameku.git}"
ADMIN_REPO="${ADMIN_REPO:-git@github.com:kiri225/admin-blog.git}"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "======== $(date '+%F %T') deploy start ========"

clone_or_pull() {
  local name="$1"
  local url="$2"
  local dir="$REPOS_DIR/$name"

  mkdir -p "$REPOS_DIR"

  if [[ -d "$dir/.git" ]]; then
    echo ">>> 更新 $name"
    git -C "$dir" remote set-url origin "$url" || true
    git -C "$dir" fetch origin
    git -C "$dir" checkout -f main || git -C "$dir" checkout -fb main origin/main
    git -C "$dir" reset --hard origin/main
    git -C "$dir" clean -fd
  else
    echo ">>> 重新克隆 $name"
    rm -rf "$dir"
    git clone --branch main --depth 1 "$url" "$dir"
  fi
  echo ">>> $name @ $(git -C "$dir" rev-parse --short HEAD)"
}

if [[ ! -f "$DEPLOY_DIR/.env" ]]; then
  echo "缺少 $DEPLOY_DIR/.env，请先复制 .env.example 并填写配置"
  exit 1
fi

# deploy-agent 内优先用挂载的宿主机 SSH
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o StrictHostKeyChecking=accept-new -i /root/.ssh/id_ed25519 -i /root/.ssh/id_rsa}"

clone_or_pull blog "$BLOG_REPO"
clone_or_pull Kirameku "$FRONTEND_REPO"
clone_or_pull admin "$ADMIN_REPO"

cp "$REPOS_DIR/blog/deploy/docker-compose.yml" "$DEPLOY_DIR/docker-compose.yml"
mkdir -p "$DEPLOY_DIR/deploy-agent"
cp "$REPOS_DIR/blog/deploy/deploy-agent/Dockerfile" "$DEPLOY_DIR/deploy-agent/Dockerfile"
if [[ ! -f "$DEPLOY_DIR/.env.example" ]]; then
  cp "$REPOS_DIR/blog/deploy/.env.example" "$DEPLOY_DIR/.env.example"
fi
cp "$REPOS_DIR/blog/deploy/deploy.sh" "$DEPLOY_DIR/deploy.sh"
chmod +x "$DEPLOY_DIR/deploy.sh"

cd "$DEPLOY_DIR"

echo ">>> 构建并启动容器"
docker compose up -d --build --remove-orphans

echo ">>> 部署完成 $(date '+%F %T')"
docker compose ps

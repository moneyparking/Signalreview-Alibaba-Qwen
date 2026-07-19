#!/usr/bin/env bash
# ==============================================================================
# ALIBABA CLOUD ECS DEPLOYMENT MANIFEST
# Target: Ubuntu 22.04 LTS / Alibaba Cloud Elastic Compute Service (ECS)
# Infrastructure: Global AI Hackathon with Qwen Cloud
# ==============================================================================
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/signalreview-qwen}"
REPO_URL="${REPO_URL:?REPO_URL must be exported before deploy}"
SERVICE_NAME="${SERVICE_NAME:-signalreview-qwen}"
PORT="${PORT:-8000}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PUBLIC_HOSTNAME="${PUBLIC_HOSTNAME:?PUBLIC_HOSTNAME must be the DNS hostname that resolves to this ECS instance}"

required_runtime_vars=(
  QWEN_BASE_URL
  QWEN_MODEL
  QWEN_API_KEY
  QWEN_TIMEOUT_MS
  QWEN_TOTAL_TIMEOUT_MS
  QWEN_MAX_REPAIR_ATTEMPTS
  SIGNALREVIEW_REASONING_PROVIDER
  API_FOOTBALL_KEY
)

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo -E bash deploy.sh"
  exit 1
fi

if [[ ! "${PUBLIC_HOSTNAME}" =~ ^[A-Za-z0-9.-]+$ || "${PUBLIC_HOSTNAME}" != *.* ]]; then
  echo "PUBLIC_HOSTNAME must be a hostname without scheme, path, port, or whitespace."
  exit 1
fi

for variable_name in "${required_runtime_vars[@]}"; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "${variable_name} must be exported before deploy."
    exit 1
  fi
done

API_FOOTBALL_BASE_URL="${API_FOOTBALL_BASE_URL:-https://v3.football.api-sports.io}"
API_FOOTBALL_DAILY_BUDGET="${API_FOOTBALL_DAILY_BUDGET:-80}"
API_FOOTBALL_CACHE_TTL_SECONDS="${API_FOOTBALL_CACHE_TTL_SECONDS:-900}"
API_FOOTBALL_TIMEOUT_MS="${API_FOOTBALL_TIMEOUT_MS:-8000}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-https://signalreview.co}"
PUBLIC_BASE_URL="https://${PUBLIC_HOSTNAME}"

apt-get update
apt-get install -y git python3 python3-venv python3-pip curl ca-certificates debian-keyring debian-archive-keyring apt-transport-https gnupg

if ! command -v caddy >/dev/null 2>&1; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    > /etc/apt/sources.list.d/caddy-stable.list
  chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  chmod o+r /etc/apt/sources.list.d/caddy-stable.list
  apt-get update
  apt-get install -y caddy
fi

mkdir -p "${APP_DIR}"
if [[ -d "${APP_DIR}/.git" ]]; then
  if ! git -C "${APP_DIR}" diff --quiet || ! git -C "${APP_DIR}" diff --cached --quiet; then
    echo "Refusing deployment because ${APP_DIR} contains uncommitted changes."
    exit 1
  fi
  git -C "${APP_DIR}" fetch origin main
  git -C "${APP_DIR}" checkout main
  git -C "${APP_DIR}" merge --ff-only origin/main
else
  if find "${APP_DIR}" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
    echo "Refusing deployment because ${APP_DIR} is non-empty and is not a Git checkout."
    exit 1
  fi
  git clone --branch main --single-branch "${REPO_URL}" "${APP_DIR}"
fi

cd "${APP_DIR}"
"${PYTHON_BIN}" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

umask 077
cat > "${APP_DIR}/.env" <<ENV
QWEN_BASE_URL=${QWEN_BASE_URL}
QWEN_MODEL=${QWEN_MODEL}
QWEN_API_KEY=${QWEN_API_KEY}
QWEN_TIMEOUT_MS=${QWEN_TIMEOUT_MS}
QWEN_TOTAL_TIMEOUT_MS=${QWEN_TOTAL_TIMEOUT_MS}
QWEN_MAX_REPAIR_ATTEMPTS=${QWEN_MAX_REPAIR_ATTEMPTS}
SIGNALREVIEW_REASONING_PROVIDER=${SIGNALREVIEW_REASONING_PROVIDER}
API_FOOTBALL_KEY=${API_FOOTBALL_KEY}
API_FOOTBALL_BASE_URL=${API_FOOTBALL_BASE_URL}
API_FOOTBALL_DAILY_BUDGET=${API_FOOTBALL_DAILY_BUDGET}
API_FOOTBALL_CACHE_TTL_SECONDS=${API_FOOTBALL_CACHE_TTL_SECONDS}
API_FOOTBALL_TIMEOUT_MS=${API_FOOTBALL_TIMEOUT_MS}
ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
ENV
chmod 600 "${APP_DIR}/.env"

cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<SERVICE
[Unit]
Description=SignalReview Alibaba Qwen Hackathon API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/uvicorn main:app --host 127.0.0.1 --port ${PORT} --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=always
RestartSec=5
User=root
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
SERVICE

cat > /etc/caddy/Caddyfile <<CADDY
${PUBLIC_HOSTNAME} {
  encode zstd gzip
  reverse_proxy 127.0.0.1:${PORT}
  header {
    Strict-Transport-Security "max-age=31536000; includeSubDomains"
    X-Content-Type-Options "nosniff"
    X-Frame-Options "DENY"
    Referrer-Policy "no-referrer"
    -Server
  }
}
CADDY

caddy validate --config /etc/caddy/Caddyfile
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"
systemctl enable caddy
systemctl restart caddy

sleep 2
systemctl --no-pager --full status "${SERVICE_NAME}" || true
systemctl --no-pager --full status caddy || true
curl -fsS "http://127.0.0.1:${PORT}/api/health"
curl -fsS "http://127.0.0.1:${PORT}/api/provider-health"
curl --retry 12 --retry-delay 5 --retry-all-errors -fsS "${PUBLIC_BASE_URL}/api/health"

cat <<OUTPUT
Deployment complete.
Local health:     http://127.0.0.1:${PORT}/api/health
Provider health:  http://127.0.0.1:${PORT}/api/provider-health
Public HTTPS:     ${PUBLIC_BASE_URL}/api/health
Judge fixtures:   ${PUBLIC_BASE_URL}/api/judge-fixtures
API docs:         ${PUBLIC_BASE_URL}/docs

Required external state:
- DNS A/AAAA for ${PUBLIC_HOSTNAME} resolves to this ECS instance.
- Alibaba ECS security group permits inbound TCP 80 and 443.
- Port ${PORT} remains private; Uvicorn listens only on 127.0.0.1.
OUTPUT

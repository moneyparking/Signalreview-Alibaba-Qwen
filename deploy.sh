#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/signalreview-qwen}"
REPO_URL="${REPO_URL:-https://github.com/moneyparking/Signalreview-Alibaba-Qwen.git}"
SERVICE_NAME="${SERVICE_NAME:-signalreview-qwen}"
PORT="${PORT:-8000}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SERVER_PUBLIC_IP="${SERVER_PUBLIC_IP:-8.220.101.4}"
QWEN_MODEL_VALUE="${QWEN_MODEL:-qwen2.5-72b-instruct}"
QWEN_BASE_URL_VALUE="${QWEN_BASE_URL:-https://dashscope-intl.aliyuncs.com/compatible-mode/v1}"
ALLOWED_ORIGINS_VALUE="${ALLOWED_ORIGINS:-*}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo -E bash deploy.sh"
  exit 1
fi

if [[ -z "${DASHSCOPE_API_KEY:-}" ]]; then
  echo "DASHSCOPE_API_KEY must be exported before deploy."
  echo "Example: export DASHSCOPE_API_KEY='your_alibaba_dashscope_key'"
  exit 1
fi

apt-get update
apt-get install -y git python3 python3-venv python3-pip curl

mkdir -p "${APP_DIR}"
if [[ -d "${APP_DIR}/.git" ]]; then
  git -C "${APP_DIR}" fetch origin main
  git -C "${APP_DIR}" reset --hard origin/main
else
  rm -rf "${APP_DIR:?}"/*
  git clone "${REPO_URL}" "${APP_DIR}"
fi

cd "${APP_DIR}"
"${PYTHON_BIN}" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cat > "${APP_DIR}/.env" <<ENV
DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
QWEN_MODEL=${QWEN_MODEL_VALUE}
QWEN_BASE_URL=${QWEN_BASE_URL_VALUE}
ALLOWED_ORIGINS=${ALLOWED_ORIGINS_VALUE}
SIGNALREVIEW_ENV=hackathon
PORT=${PORT}
ENV
chmod 600 "${APP_DIR}/.env"

cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<SERVICE
[Unit]
Description=SignalReview Alibaba Qwen Hackathon API
After=network.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/uvicorn main:app --host 0.0.0.0 --port ${PORT}
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

sleep 2
systemctl --no-pager --full status "${SERVICE_NAME}" || true
curl -fsS "http://127.0.0.1:${PORT}/api/health" || true

echo "Deployment complete."
echo "Local health:  http://127.0.0.1:${PORT}/api/health"
echo "Public health: http://${SERVER_PUBLIC_IP}:${PORT}/api/health"
echo "API docs:      http://${SERVER_PUBLIC_IP}:${PORT}/docs"

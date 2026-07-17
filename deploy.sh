#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/signalreview-qwen}"
REPO_URL="${REPO_URL:?REPO_URL must be exported before deploy}"
SERVICE_NAME="${SERVICE_NAME:-signalreview-qwen}"
PORT="${PORT:-8000}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

required_runtime_vars=(
  QWEN_BASE_URL
  QWEN_MODEL
  QWEN_API_KEY
  QWEN_TIMEOUT_MS
  QWEN_TOTAL_TIMEOUT_MS
  QWEN_MAX_REPAIR_ATTEMPTS
  SIGNALREVIEW_REASONING_PROVIDER
)

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo -E bash deploy.sh"
  exit 1
fi

for variable_name in "${required_runtime_vars[@]}"; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "${variable_name} must be exported before deploy."
    exit 1
  fi
done

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

umask 077
cat > "${APP_DIR}/.env" <<ENV
QWEN_BASE_URL=${QWEN_BASE_URL}
QWEN_MODEL=${QWEN_MODEL}
QWEN_API_KEY=${QWEN_API_KEY}
QWEN_TIMEOUT_MS=${QWEN_TIMEOUT_MS}
QWEN_TOTAL_TIMEOUT_MS=${QWEN_TOTAL_TIMEOUT_MS}
QWEN_MAX_REPAIR_ATTEMPTS=${QWEN_MAX_REPAIR_ATTEMPTS}
SIGNALREVIEW_REASONING_PROVIDER=${SIGNALREVIEW_REASONING_PROVIDER}
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
curl -fsS "http://127.0.0.1:${PORT}/api/health"

echo "Deployment complete."
echo "Local health: http://127.0.0.1:${PORT}/api/health"
echo "API docs:     http://127.0.0.1:${PORT}/docs"

#!/usr/bin/env bash
# Startup script for the Render deployment.
# Streamlit reads its [auth] settings from .streamlit/secrets.toml, which we
# generate here from environment variables so that no secret is committed.
set -euo pipefail

mkdir -p .streamlit

if [ -n "${GOOGLE_CLIENT_ID:-}" ] && [ -n "${GOOGLE_CLIENT_SECRET:-}" ]; then
  cat > .streamlit/secrets.toml <<EOF
[auth]
redirect_uri = "${AUTH_REDIRECT_URI:-}"
cookie_secret = "${AUTH_COOKIE_SECRET:-}"
client_id = "${GOOGLE_CLIENT_ID}"
client_secret = "${GOOGLE_CLIENT_SECRET}"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
EOF
  echo "[auth] secrets.toml generated from environment variables."
else
  echo "[auth] Google OAuth env vars not set - login gate stays disabled."
fi

exec streamlit run app.py \
  --server.port "${PORT:-8501}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false

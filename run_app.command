#!/bin/bash
set -e

cd "$(dirname "$0")"

PID_FILE=".venv/.textsignal.pid"
PORT_FILE=".venv/.textsignal.port"

if [ -f "$PID_FILE" ] && [ -f "$PORT_FILE" ]; then
  EXISTING_PID="$(/bin/cat "$PID_FILE")"
  EXISTING_PORT="$(/bin/cat "$PORT_FILE")"
  EXISTING_URL="http://127.0.0.1:${EXISTING_PORT}"
  if /bin/kill -0 "$EXISTING_PID" 2>/dev/null && /usr/bin/curl -fsS "${EXISTING_URL}/_stcore/health" >/dev/null 2>&1; then
    echo "TextSignal is already running. Opening it now."
    if [ "${TEXTSIGNAL_NO_BROWSER:-0}" != "1" ]; then
      /usr/bin/open "$EXISTING_URL"
    fi
    exit 0
  fi
  /bin/rm -f "$PID_FILE" "$PORT_FILE"
fi

if ! /usr/bin/env python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  echo "TextSignal needs Python 3.10 or newer."
  echo "Install it from https://www.python.org/downloads/ and try again."
  read -r -p "Press Return to close..."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Creating TextSignal's private Python environment..."
  /usr/bin/env python3 -m venv .venv
fi

source .venv/bin/activate
export ARROW_DEFAULT_MEMORY_POOL="${ARROW_DEFAULT_MEMORY_POOL:-system}"

REQUIREMENTS_HASH="$(/usr/bin/shasum -a 256 requirements.txt | /usr/bin/awk '{print $1}')"
READY_FILE=".venv/.textsignal-requirements-${REQUIREMENTS_HASH}"
if [ ! -f "$READY_FILE" ]; then
  echo "First launch: downloading TextSignal's packages. Later launches will be faster."
  python -m pip --disable-pip-version-check install --prefer-binary -r requirements.txt
  /bin/rm -f .venv/.textsignal-requirements-* .venv/.textsignal-ready
  /usr/bin/touch "$READY_FILE"
else
  echo "Using the existing TextSignal environment."
fi

if [ -n "${TEXTSIGNAL_PORT:-}" ]; then
  PORT="$TEXTSIGNAL_PORT"
else
  PORT="$(python - <<'PY'
import socket

for candidate in [8600, *range(8501, 8601)]:
    sock = socket.socket()
    try:
        sock.bind(("127.0.0.1", candidate))
    except OSError:
        continue
    finally:
        sock.close()
    print(candidate)
    break
else:
    raise SystemExit("No free local port was found between 8501 and 8600.")
PY
)"
fi

URL="http://127.0.0.1:${PORT}"
MAX_UPLOAD_MB="${TEXTSIGNAL_MAX_UPLOAD_MB:-50}"

echo "Starting TextSignal at ${URL}..."
python -m streamlit run app.py \
  --server.headless=true \
  --server.address=127.0.0.1 \
  --server.port="$PORT" \
  --server.maxUploadSize="$MAX_UPLOAD_MB" \
  --server.fileWatcherType=none \
  --browser.gatherUsageStats=false &
APP_PID=$!

echo "$APP_PID" > "$PID_FILE"
echo "$PORT" > "$PORT_FILE"

cleanup() {
  /bin/rm -f "$PID_FILE" "$PORT_FILE"
  if /bin/kill -0 "$APP_PID" 2>/dev/null; then
    /bin/kill "$APP_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

ATTEMPT=1
while [ "$ATTEMPT" -le 120 ]; do
  if /usr/bin/curl -fsS "${URL}/_stcore/health" >/dev/null 2>&1; then
    if [ "${TEXTSIGNAL_NO_BROWSER:-0}" != "1" ]; then
      echo "TextSignal is ready. Opening your browser..."
      /usr/bin/open "$URL"
    else
      echo "TextSignal is ready at ${URL}."
    fi
    wait "$APP_PID"
    exit $?
  fi
  if ! /bin/kill -0 "$APP_PID" 2>/dev/null; then
    echo "TextSignal stopped before it became ready. Review the message above."
    wait "$APP_PID"
    exit $?
  fi
  ATTEMPT=$((ATTEMPT + 1))
  /bin/sleep 0.25
done

echo "TextSignal took too long to start. Review the message above, then try again."
exit 1

#!/bin/bash
WIKI_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$WIKI_DIR/tools/server.pid"
LOG_FILE="$WIKI_DIR/tools/server.log"
PORT=3500

case "$1" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
      echo "Wiki server is already running (PID: $(cat $PID_FILE)) on http://localhost:$PORT"
      exit 0
    fi
    cd "$WIKI_DIR"
    nohup python3 -m http.server $PORT > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Wiki server started (PID: $!) on http://localhost:$PORT"
    ;;
  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      kill $PID 2>/dev/null || true
      rm -f "$PID_FILE"
      echo "Wiki server stopped."
    else
      echo "Wiki server is not running."
    fi
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
      echo "Wiki server is running (PID: $(cat $PID_FILE)) on http://localhost:$PORT"
    else
      echo "Wiki server is stopped."
    fi
    ;;
  restart)
    $0 stop
    sleep 1
    $0 start
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac

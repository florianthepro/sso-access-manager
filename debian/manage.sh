#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV="$BASE/.env"
PIDFILE="$BASE/data/access-manager.pid"
LOG="$BASE/data/access-manager.log"
[ -f "$ENV" ] || { echo "Zuerst ./setup.sh starten" >&2; exit 1; }
set -a
. "$ENV"
set +a
PY="$BASE/.venv/bin/python"
UV="$BASE/.venv/bin/uvicorn"
[ -x "$PY" ] && [ -x "$UV" ] || { echo "Laufzeit fehlt. ./setup.sh erneut starten." >&2; exit 1; }
alive(){ [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null; }
case "${1:-status}" in
 start)
   if alive; then echo "Laeuft bereits mit PID $(cat "$PIDFILE")"; exit 0; fi
   "$PY" - "$BIND_HOST" "$BIND_PORT" <<'PY'
import socket, sys
h,p=sys.argv[1],int(sys.argv[2]); h='127.0.0.1' if h=='localhost' else h
s=socket.socket()
try:s.bind((h,p))
except OSError as e:raise SystemExit(f'Port nicht verfuegbar: {e}')
finally:s.close()
PY
   umask 077
   cd "$BASE"
   nohup "$UV" backend:app --host "$BIND_HOST" --port "$BIND_PORT" --workers 1 --proxy-headers --forwarded-allow-ips="127.0.0.1" >>"$LOG" 2>&1 &
   echo $! > "$PIDFILE"
   sleep 1
   if alive; then echo "Gestartet: http://$BIND_HOST:$BIND_PORT (PID $(cat "$PIDFILE"))"; else echo "Start fehlgeschlagen. Siehe $LOG" >&2; rm -f "$PIDFILE"; exit 1; fi
   ;;
 stop)
   if ! alive; then echo "Nicht gestartet"; rm -f "$PIDFILE"; exit 0; fi
   PID=$(cat "$PIDFILE"); kill "$PID"
   i=0; while kill -0 "$PID" 2>/dev/null && [ "$i" -lt 20 ]; do sleep 1; i=$((i+1)); done
   kill -0 "$PID" 2>/dev/null && kill -9 "$PID" || true
   rm -f "$PIDFILE"; echo "Gestoppt"
   ;;
 restart) "$0" stop; "$0" start ;;
 status) if alive; then echo "Laeuft: PID $(cat "$PIDFILE"), http://$BIND_HOST:$BIND_PORT"; else echo "Nicht gestartet"; exit 1; fi ;;
 logs) touch "$LOG"; tail -n 100 -f "$LOG" ;;
 foreground) cd "$BASE"; exec "$UV" backend:app --host "$BIND_HOST" --port "$BIND_PORT" --workers 1 ;;
 *) echo "Nutzung: $0 {start|stop|restart|status|logs|foreground}" >&2; exit 2 ;;
esac

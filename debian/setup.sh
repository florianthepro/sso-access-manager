#!/bin/sh
set -eu
B=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd); R="$B/.runtime"; V="$B/.venv"; E="$B/.env"; D="$B/data"
[ "$(id -u)" -ne 0 ] || { echo 'Nicht als root/sudo starten.' >&2; exit 1; }
mkdir -p "$R" "$D"; chmod 700 "$D"
case "$(uname -m)" in x86_64) A=x86_64-unknown-linux-gnu;; aarch64|arm64) A=aarch64-unknown-linux-gnu;; *) echo 'Nur x86_64/arm64.'; exit 1;; esac
P="$R/python/bin/python3"
if [ ! -x "$P" ]; then
 U="https://github.com/astral-sh/python-build-standalone/releases/download/20261021/cpython-3.13.17%2B20261021-$A-install_only.tar.gz"; F="$R/python.tgz"
 echo 'Lade private Python-Laufzeit...'; if command -v curl >/dev/null; then curl -fL --retry 3 "$U" -o "$F"; elif command -v wget >/dev/null; then wget -O "$F" "$U"; else echo 'curl oder wget fehlt.'; exit 1; fi
 tar -xzf "$F" -C "$R"; rm "$F"
fi
[ -x "$V/bin/python" ] || "$P" -m venv "$V"
"$V/bin/python" -m pip install --no-input -r "$B/requirements-runtime.txt"
printf 'Bind-IP [127.0.0.1]: '; read H || true; H=${H:-127.0.0.1}
printf 'Port [8765]: '; read Q || true; Q=${Q:-8765}
case "$Q" in *[!0-9]*|'') echo 'Port muss numerisch sein'; exit 1;; esac
[ "$Q" -ge 1024 ] && [ "$Q" -le 65535 ] || { echo 'Nur Ports 1024-65535.'; exit 1; }
"$V/bin/python" - "$H" "$Q" <<'PY'
import socket,sys,ipaddress
h,p=sys.argv[1],int(sys.argv[2])
if h not in ('localhost','0.0.0.0'): ipaddress.ip_address(h)
if h=='localhost':h='127.0.0.1'
s=socket.socket();s.bind((h,p));s.close()
PY
[ ! -f "$E" ] || cp "$E" "$E.backup.$(date +%s)"
S=$($V/bin/python -c 'import secrets;print(secrets.token_urlsafe(48))')
cat > "$E" <<EOF
APP_SECRET=$S
TRUSTED_HOSTS=$H,localhost,127.0.0.1
DATABASE_PATH=$D/access.sqlite3
COOKIE_SECURE=false
SESSION_HOURS=12
BIND_HOST=$H
BIND_PORT=$Q
EOF
chmod 600 "$E"; [ -f "$D/access.sqlite3" ] || cp "$D/empty.sqlite3" "$D/access.sqlite3"; chmod 600 "$D/access.sqlite3"
echo "Fertig. Start: ./manage.sh start | URL: http://$H:$Q"
printf 'Jetzt starten? [J/n]: '; read X || true; case ${X:-j} in n|N);; *) "$B/manage.sh" start;; esac

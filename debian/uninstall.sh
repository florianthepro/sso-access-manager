#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
"$BASE/manage.sh" stop 2>/dev/null || true
printf 'Datenbank und Konfiguration ebenfalls loeschen? [y/N]: '
read YES || true
rm -rf "$BASE/.runtime" "$BASE/.venv"
case "${YES:-n}" in y|Y) rm -f "$BASE/.env" "$BASE"/data/access.sqlite3 "$BASE"/data/access.sqlite3-* "$BASE"/data/access-manager.log ;; esac
echo "Private Laufzeit entfernt. Projektdateien wurden nicht geloescht."

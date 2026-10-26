#!/bin/sh
set -eu

REPO="florianthepro/sso-access-manager"
BRANCH="main"
DEST="${SSOAC_DIR:-/ssoac}"
TMP="${TMPDIR:-/tmp}/ssoac-install.$$"

say(){ printf '%s\n' "$*"; }
fail(){ printf 'Fehler: %s\n' "$*" >&2; exit 1; }
have(){ command -v "$1" >/dev/null 2>&1; }
cleanup(){ rm -rf "$TMP"; }
trap cleanup EXIT HUP INT TERM

if [ -r /dev/tty ] && [ -w /dev/tty ]; then
    TTY=/dev/tty
else
    fail "Kein interaktives Terminal verfuegbar. Setup direkt mit 'python3 setup.py' starten."
fi

ask(){
    prompt=$1
    default=$2
    printf '%s' "$prompt" >"$TTY"
    if IFS= read -r value <"$TTY"; then :; else value=""; fi
    [ -n "$value" ] || value=$default
    REPLY=$value
}

[ "$(id -u)" -ne 0 ] || fail "Bitte als normaler Benutzer starten. Sudo wird nur bei Bedarf fuer /ssoac angefordert."
have python3 || fail "Python 3.11 oder neuer fehlt."
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Fehler: Python 3.11 oder neuer ist erforderlich")
PY
have unzip || fail "unzip fehlt."
if ! have curl && ! have wget; then fail "curl oder wget fehlt."; fi

if [ -e "$DEST" ]; then
    say "Das Ziel $DEST existiert bereits."
    ask 'Bestehende Installation wirklich stoppen und komplett zuruecksetzen? [y/N]: ' n
    case "$REPLY" in y|Y|yes|YES|ja|JA) ;; *) say "Abgebrochen. Es wurde nichts veraendert."; exit 0;; esac
    if [ -f "$DEST/.venv/bin/python" ] && [ -f "$DEST/run.py" ]; then
        "$DEST/.venv/bin/python" "$DEST/run.py" stop >/dev/null 2>&1 || true
    fi
    ask 'Vorhandene Datenbank als Backup neben dem Ziel sichern? [Y/n]: ' y
    case "$REPLY" in n|N|no|NO|nein|NEIN) ;;
      *) if [ -f "$DEST/data/access.sqlite3" ]; then
           BACKUP_FILE="${DEST%/}-access-backup-$(date +%Y%m%d-%H%M%S).sqlite3"
           if cp "$DEST/data/access.sqlite3" "$BACKUP_FILE" 2>/dev/null; then say "Backup: $BACKUP_FILE";
           elif have sudo; then sudo cp "$DEST/data/access.sqlite3" "$BACKUP_FILE" <"$TTY" && sudo chown "$(id -u):$(id -g)" "$BACKUP_FILE" <"$TTY"; else fail "Backup konnte nicht geschrieben werden"; fi
         fi ;;
    esac
fi

mkdir -p "$TMP/unpack"
ARCHIVE="$TMP/repo.zip"
URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.zip"
say "Lade $REPO ($BRANCH) ..."
if have curl; then curl -fL --retry 3 --connect-timeout 15 "$URL" -o "$ARCHIVE"
else wget -O "$ARCHIVE" "$URL"; fi
unzip -q "$ARCHIVE" -d "$TMP/unpack"
SOURCE=$(find "$TMP/unpack" -mindepth 1 -maxdepth 1 -type d | head -n 1)
[ -n "$SOURCE" ] && [ -f "$SOURCE/setup.py" ] || fail "Repository enthaelt setup.py nicht im Hauptverzeichnis"

PARENT=$(dirname "$DEST")
if mkdir -p "$PARENT" 2>/dev/null && [ -w "$PARENT" ]; then
    rm -rf "$DEST"
    mkdir -p "$DEST"
    cp -a "$SOURCE/." "$DEST/"
else
    have sudo || fail "$PARENT ist nicht beschreibbar und sudo fehlt"
    sudo rm -rf "$DEST" <"$TTY"
    sudo mkdir -p "$DEST" <"$TTY"
    sudo cp -a "$SOURCE/." "$DEST/" <"$TTY"
    sudo chown -R "$(id -u):$(id -g)" "$DEST" <"$TTY"
fi
chmod +x "$DEST/setup.sh" "$DEST/install.sh" 2>/dev/null || true
say "Dateien liegen in $DEST. Starte OOBE ..."
cd "$DEST"
exec python3 setup.py <"$TTY" >"$TTY" 2>"$TTY"

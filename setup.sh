#!/bin/sh
set -eu
command -v python3 >/dev/null 2>&1 || { echo 'Python 3.11+ fehlt.' >&2; exit 1; }
exec python3 "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/setup.py"

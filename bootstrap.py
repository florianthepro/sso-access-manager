import io
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

REPOSITORY_ZIP = "https://github.com/florianthepro/sso-access-manager/archive/refs/heads/main.zip"
DESTINATION = Path("/ssoac") if os.name != "nt" else Path.home() / "ssoac"
REQUIRED_FILES = ("setup.py", "run.py", "app.py", "requirements.txt", "data/empty.sqlite3")


def fail(message):
    raise SystemExit(f"Fehler: {message}")


def run(command):
    subprocess.run(command, check=True)


def valid_project(path):
    return path.is_dir() and all((path / item).is_file() for item in REQUIRED_FILES)


def locate_project(extracted):
    if valid_project(extracted):
        return extracted
    candidates = [path for path in extracted.rglob("setup.py") if valid_project(path.parent)]
    if len(candidates) != 1:
        fail("Repository-Struktur ungueltig oder nicht eindeutig")
    return candidates[0].parent


def remove_destination():
    if not DESTINATION.exists():
        return
    answer = input(f"{DESTINATION} ersetzen? [y/N]: ").strip().lower()
    if answer not in {"y", "yes", "j", "ja"}:
        raise SystemExit("Abbruch")
    try:
        shutil.rmtree(DESTINATION)
    except PermissionError:
        if os.name == "nt":
            fail(f"Keine Rechte zum Entfernen von {DESTINATION}")
        print("Sudo: bestehendes Ziel entfernen")
        run(["sudo", "rm", "-rf", "--", str(DESTINATION)])


def install_project(source):
    if os.name == "nt":
        DESTINATION.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, DESTINATION)
        return
    try:
        DESTINATION.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, DESTINATION)
    except PermissionError:
        print("Sudo: Zielordner anlegen")
        run(["sudo", "mkdir", "-p", "--", str(DESTINATION)])
        run(["sudo", "cp", "-a", str(source) + "/.", str(DESTINATION) + "/"])
        run(["sudo", "chown", "-R", f"{os.getuid()}:{os.getgid()}", str(DESTINATION)])


def main():
    if sys.version_info < (3, 11):
        fail("Python 3.11 oder neuer erforderlich")
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        fail("Nicht mit sudo starten")

    print("Download")
    request = urllib.request.Request(REPOSITORY_ZIP, headers={"User-Agent": "ssoac-bootstrap"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            archive_data = response.read()
    except Exception as exc:
        fail(f"Download fehlgeschlagen: {exc}")

    with tempfile.TemporaryDirectory(prefix="ssoac-") as temporary:
        extracted = Path(temporary) / "repository"
        extracted.mkdir()
        try:
            with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
                archive.extractall(extracted)
        except Exception as exc:
            fail(f"Archiv ungueltig: {exc}")

        source = locate_project(extracted)
        print("Pruefung OK")
        remove_destination()
        install_project(source)

    if not valid_project(DESTINATION):
        fail(f"Installation unvollstaendig: {DESTINATION}")

    print(f"Installiert: {DESTINATION}")
    os.chdir(DESTINATION)
    os.execv(sys.executable, [sys.executable, str(DESTINATION / "setup.py")])


if __name__ == "__main__":
    main()

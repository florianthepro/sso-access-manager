import getpass
import io
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

REPOSITORY_ZIP = "https://github.com/florianthepro/sso-access-manager/archive/refs/heads/main.zip"
DEFAULT_DESTINATION = Path("/ssoac") if os.name != "nt" else Path.home() / "ssoac"


def ask(prompt, default=""):
    try:
        value = input(prompt).strip()
    except EOFError:
        value = ""
    return value or default


def run(command, **kwargs):
    return subprocess.run(command, check=True, **kwargs)


def stop_existing(destination):
    run_py = destination / "run.py"
    if not run_py.exists():
        return
    python_candidates = [
        destination / ".venv" / "Scripts" / "python.exe",
        destination / ".venv" / "bin" / "python",
    ]
    for candidate in python_candidates:
        if candidate.exists():
            subprocess.run([str(candidate), str(run_py), "stop"], check=False)
            return


def backup_database(destination):
    database = destination / "data" / "access.sqlite3"
    if not database.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = destination.parent / f"{destination.name}-access-backup-{stamp}.sqlite3"
    shutil.copy2(database, backup)
    print(f"Datenbank-Backup: {backup}")


def remove_destination(destination):
    try:
        shutil.rmtree(destination)
        return
    except PermissionError:
        if os.name == "nt":
            raise SystemExit(f"Keine Rechte zum Entfernen von {destination}. Terminal als derselbe Besitzer starten.")
    print(f"Administratorrechte werden nur zum Ersetzen von {destination} benoetigt.")
    run(["sudo", sys.executable, "-c", "import shutil,sys; shutil.rmtree(sys.argv[1])", str(destination)])


def copy_project(source, destination):
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination)
    except PermissionError:
        if os.name == "nt":
            raise SystemExit(f"Keine Schreibrechte fuer {destination.parent}.")
        with tempfile.TemporaryDirectory() as staging_dir:
            staging = Path(staging_dir) / "ssoac"
            shutil.copytree(source, staging)
            run(["sudo", "mkdir", "-p", str(destination)])
            run(["sudo", "cp", "-a", f"{staging}/.", str(destination)])
            run(["sudo", "chown", "-R", f"{os.getuid()}:{os.getgid()}", str(destination)])


def main():
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11 oder neuer ist erforderlich.")

    destination_text = ask(f"Installationsordner [{DEFAULT_DESTINATION}]: ", str(DEFAULT_DESTINATION))
    destination = Path(destination_text).expanduser().resolve()

    if destination.exists():
        answer = ask(f"{destination} existiert. Installation stoppen und komplett zuruecksetzen? [y/N]: ", "n").lower()
        if answer not in {"y", "yes", "j", "ja"}:
            print("Abgebrochen. Es wurde nichts veraendert.")
            return
        if ask("Vorhandene Datenbank vorher sichern? [Y/n]: ", "y").lower() not in {"n", "no", "nein"}:
            backup_database(destination)
        stop_existing(destination)
        remove_destination(destination)

    print("Lade Repository ...")
    request = urllib.request.Request(REPOSITORY_ZIP, headers={"User-Agent": "sso-access-manager-bootstrap"})
    with urllib.request.urlopen(request, timeout=60) as response:
        archive_data = response.read()

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary = Path(temporary_directory)
        with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
            archive.extractall(temporary)
        roots = [item for item in temporary.iterdir() if item.is_dir()]
        if len(roots) != 1 or not (roots[0] / "setup.py").exists():
            raise SystemExit("Das Repository besitzt nicht die erwartete All-in-one-Struktur.")
        copy_project(roots[0], destination)

    print(f"Dateien installiert: {destination}")
    print("Starte OOBE ...")
    os.chdir(destination)
    os.execv(sys.executable, [sys.executable, str(destination / "setup.py")])


if __name__ == "__main__":
    main()

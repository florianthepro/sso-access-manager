import io, os, shutil, subprocess, sys, tempfile, urllib.request, zipfile
from pathlib import Path

URL = "https://github.com/florianthepro/sso-access-manager/archive/refs/heads/main.zip"
DEST = Path("/ssoac") if os.name != "nt" else Path.home() / "ssoac"


def run(command):
    subprocess.run(command, check=True)


def remove_destination():
    if not DEST.exists():
        return
    answer = input(f"{DEST} ersetzen? [y/N]: ").strip().lower()
    if answer not in {"y", "yes", "j", "ja"}:
        raise SystemExit("Abbruch")
    try:
        shutil.rmtree(DEST)
    except PermissionError:
        if os.name == "nt":
            raise SystemExit(f"Keine Rechte fuer {DEST}. Terminal als Besitzer oder Administrator starten.")
        print(f"Sudo wird nur zum Entfernen von {DEST} verwendet.")
        run(["sudo", "rm", "-rf", "--", str(DEST)])


def install(source):
    try:
        DEST.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, DEST)
    except PermissionError:
        if os.name == "nt":
            raise SystemExit(f"Keine Schreibrechte fuer {DEST.parent}.")
        print(f"Sudo wird nur zum Anlegen von {DEST} verwendet.")
        run(["sudo", "mkdir", "-p", "--", str(DEST)])
        run(["sudo", "cp", "-a", f"{source}/.", str(DEST)])
        run(["sudo", "chown", "-R", f"{os.getuid()}:{os.getgid()}", str(DEST)])


def main():
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11+ erforderlich")
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise SystemExit("Nicht mit sudo starten. Der Installer fordert sudo nur bei Bedarf an.")
    remove_destination()
    print("Download ...")
    request = urllib.request.Request(URL, headers={"User-Agent": "ssoac-bootstrap"})
    archive = urllib.request.urlopen(request, timeout=60).read()
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        zipfile.ZipFile(io.BytesIO(archive)).extractall(temp)
        source = next(item for item in temp.iterdir() if item.is_dir())
        if not (source / "setup.py").exists():
            raise SystemExit("Repository ist nicht vollstaendig")
        install(source)
    print(f"Installiert: {DEST}")
    os.chdir(DEST)
    os.execv(sys.executable, [sys.executable, str(DEST / "setup.py")])


if __name__ == "__main__":
    main()

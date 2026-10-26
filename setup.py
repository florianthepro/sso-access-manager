import getpass
import ipaddress
import os
import secrets
import shutil
import socket
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
VENV = BASE / ".venv"
DATA = BASE / "data"
ENV = BASE / ".env"
REQ = BASE / "requirements-runtime.txt"


def fail(message):
    raise SystemExit(f"Fehler: {message}")


def ask(prompt, default):
    value = input(f"{prompt} [{default}]: ").strip()
    return value or default


def venv_python():
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def validate_host(host):
    if host in {"localhost", "0.0.0.0", "::", "::1"}:
        return
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if not all(part and part.replace("-", "").isalnum() for part in host.split(".")):
            fail("ungueltige Bind-Adresse")


def check_port(host, port):
    bind_host = "127.0.0.1" if host == "localhost" else host
    family = socket.AF_INET6 if ":" in bind_host else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    try:
        sock.bind((bind_host, port))
    except OSError as exc:
        fail(f"{host}:{port} ist nicht verfuegbar: {exc}")
    finally:
        sock.close()


def write_env(host, port):
    if ENV.exists():
        backup = ENV.with_name(f".env.backup.{secrets.token_hex(4)}")
        shutil.copy2(ENV, backup)
        print(f"Vorhandene Konfiguration gesichert: {backup.name}")
    db = (DATA / "access.sqlite3").resolve()
    values = {
        "APP_SECRET": secrets.token_urlsafe(48),
        "TRUSTED_HOSTS": f"{host},localhost,127.0.0.1",
        "DATABASE_PATH": str(db),
        "COOKIE_SECURE": "false",
        "SESSION_HOURS": "12",
        "BIND_HOST": host,
        "BIND_PORT": str(port),
    }
    ENV.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    if os.name != "nt":
        os.chmod(ENV, 0o600)


def main():
    if sys.version_info < (3, 11):
        fail("Python 3.11 oder neuer ist erforderlich")
    print("Access Manager Setup")
    print(f"Projektordner: {BASE}")
    print(f"Python: {sys.executable}")
    print(f"Benutzer: {getpass.getuser()}")
    DATA.mkdir(exist_ok=True)
    if not VENV.exists():
        print("Erstelle private Python-Umgebung im Projektordner ...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    py = venv_python()
    print("Installiere Projektabhaengigkeiten nur in .venv ...")
    subprocess.run([str(py), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-r", str(REQ)], check=True)
    host = ask("Bind-Adresse", "127.0.0.1")
    validate_host(host)
    try:
        port = int(ask("Port", "8765"))
    except ValueError:
        fail("Port muss numerisch sein")
    if not 1024 <= port <= 65535:
        fail("nur nicht privilegierte Ports 1024 bis 65535 sind erlaubt")
    check_port(host, port)
    write_env(host, port)
    target = DATA / "access.sqlite3"
    if not target.exists():
        shutil.copy2(DATA / "empty.sqlite3", target)
        if os.name != "nt":
            os.chmod(target, 0o600)
    print("\nEinrichtung abgeschlossen.")
    print(f"Start: {py} run.py start")
    print(f"Adresse: http://{host}:{port}")
    if input("Jetzt starten? [J/n]: ").strip().lower() not in {"n", "nein", "no"}:
        os.execv(str(py), [str(py), str(BASE / "run.py"), "start"])


if __name__ == "__main__":
    main()

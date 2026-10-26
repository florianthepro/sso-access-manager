import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
ENV = BASE / ".env"
DATA = BASE / "data"
PIDFILE = DATA / "access-manager.pid"
LOG = DATA / "access-manager.log"


def load_env():
    if not ENV.exists():
        raise SystemExit("Zuerst setup.py starten")
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ[key] = value


def pid_value():
    try:
        return int(PIDFILE.read_text().strip())
    except (OSError, ValueError):
        return None


def alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def ensure_port_free(host, port):
    host = "127.0.0.1" if host == "localhost" else host
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
    except OSError as exc:
        raise SystemExit(f"Port ist nicht verfuegbar: {exc}")
    finally:
        sock.close()


def start(foreground=False):
    pid = pid_value()
    if alive(pid):
        print(f"Laeuft bereits mit PID {pid}")
        return
    host = os.environ["BIND_HOST"]
    port = int(os.environ["BIND_PORT"])
    ensure_port_free(host, port)
    command = [sys.executable, "-m", "uvicorn", "backend:app", "--host", host, "--port", str(port), "--workers", "1"]
    if foreground:
        os.chdir(BASE)
        os.execv(sys.executable, command)
    DATA.mkdir(exist_ok=True)
    log = LOG.open("a", encoding="utf-8")
    flags = 0
    kwargs = {"cwd": BASE, "stdout": log, "stderr": subprocess.STDOUT, "stdin": subprocess.DEVNULL, "start_new_session": True}
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        kwargs.pop("start_new_session")
        kwargs["creationflags"] = flags
    process = subprocess.Popen(command, **kwargs)
    PIDFILE.write_text(str(process.pid), encoding="ascii")
    time.sleep(1)
    if not alive(process.pid):
        PIDFILE.unlink(missing_ok=True)
        raise SystemExit(f"Start fehlgeschlagen. Log: {LOG}")
    print(f"Gestartet: http://{host}:{port} (PID {process.pid})")


def stop():
    pid = pid_value()
    if not alive(pid):
        PIDFILE.unlink(missing_ok=True)
        print("Nicht gestartet")
        return
    os.kill(pid, signal.SIGTERM)
    for _ in range(20):
        if not alive(pid):
            break
        time.sleep(0.25)
    if alive(pid) and os.name != "nt":
        os.kill(pid, signal.SIGKILL)
    PIDFILE.unlink(missing_ok=True)
    print("Gestoppt")


def logs():
    LOG.touch(exist_ok=True)
    with LOG.open("r", encoding="utf-8", errors="replace") as stream:
        stream.seek(0, 2)
        try:
            while True:
                line = stream.readline()
                if line:
                    print(line, end="")
                else:
                    time.sleep(0.3)
        except KeyboardInterrupt:
            pass


def main():
    load_env()
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "start": start()
    elif action == "foreground": start(True)
    elif action == "stop": stop()
    elif action == "restart": stop(); start()
    elif action == "status":
        pid = pid_value()
        print(f"Laeuft mit PID {pid}" if alive(pid) else "Nicht gestartet")
    elif action == "logs": logs()
    else: raise SystemExit("Nutzung: run.py start|stop|restart|status|logs|foreground")


if __name__ == "__main__":
    main()

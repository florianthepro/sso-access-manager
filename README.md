# SSO Access Manager

Ein All-in-one-Repository. Es gibt keinen gesonderten `debian/`-Ordner. `backend.py`, `setup.py`, `run.py`, Datenbankschema und Installationsskripte liegen gemeinsam im Repository-Hauptverzeichnis.

## Ein Befehl unter Linux

```bash
curl -fsSL https://raw.githubusercontent.com/florianthepro/sso-access-manager/main/install.sh | sh
```

Alternativ mit wget:

```bash
wget -qO- https://raw.githubusercontent.com/florianthepro/sso-access-manager/main/install.sh | sh
```

Standardziel ist `/ssoac`. Ist `/ssoac` nicht beschreibbar, verwendet das Installationsskript `sudo` ausschließlich zum Erstellen beziehungsweise Ersetzen dieses Ordners und übergibt ihn danach dem aufrufenden Benutzer. Die Anwendung selbst wird nicht als root betrieben.

Wenn `/ssoac` bereits existiert, fragt das Skript vor jedem Reset ausdrücklich nach. Standardantwort ist Abbruch. Vor einem bestätigten Reset wird zusätzlich angeboten, `data/access.sqlite3` als datierte Backupdatei neben `/ssoac` zu sichern.

Für einen anderen Zielordner:

```bash
curl -fsSL https://raw.githubusercontent.com/florianthepro/sso-access-manager/main/install.sh | SSOAC_DIR="$HOME/ssoac" sh
```

## Manuelle Installation

Voraussetzungen: Python 3.11+, Internetzugang beim ersten Setup und `unzip`.

```bash
git clone https://github.com/florianthepro/sso-access-manager.git /ssoac
cd /ssoac
python3 setup.py
```

`setup.py` erstellt `.venv`, installiert Python-Abhängigkeiten nur dort, prüft Bind-IP und Port, erzeugt `.env` mit zufälligem Secret und legt `data/access.sqlite3` nur an, wenn sie noch nicht vorhanden ist. Es werden keine Systempakete, Webserverkonfigurationen oder Firewallregeln verändert.

## Start und Betrieb

Linux/macOS:

```bash
cd /ssoac
.venv/bin/python run.py start
.venv/bin/python run.py status
.venv/bin/python run.py logs
.venv/bin/python run.py restart
.venv/bin/python run.py stop
```

Windows:

```powershell
py -3 setup.py
.venv\Scripts\python.exe run.py start
```

## Port- und Dienstschutz

- Standardbindung: `127.0.0.1:8765`
- nur Ports `1024` bis `65535`
- echter Bind-Test vor Einrichtung und Start
- belegte Ports werden abgelehnt
- keine fremden Prozesse werden beendet
- keine nginx-, Apache-, Caddy- oder IIS-Dateien werden verändert
- keine globale Python-Paketinstallation
- kein automatischer Systemdienst

Für Cloudflare Tunnel das Standardziel `http://127.0.0.1:8765` verwenden.

## Repository-Struktur

```text
backend.py
setup.py
setup.sh
setup.ps1
setup.bat
run.py
install.sh
requirements-runtime.txt
data/empty.sqlite3
```

Die Dateien `.env`, `.venv/`, `data/access.sqlite3`, Logs und PID-Dateien werden nicht in Git gespeichert.

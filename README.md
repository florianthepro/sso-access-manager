# Access Manager

Plattformneutrales Grundprojekt für Windows, Linux, macOS und andere Systeme mit Python 3.11 oder neuer. Es installiert nichts global und verändert keine vorhandenen Webserver oder Systemdienste.

## Voraussetzung

- Python 3.11 oder neuer
- Internetzugriff beim ersten Setup, damit Python-Pakete in die lokale `.venv` geladen werden können

## Schnellstart

### Linux, Debian, Ubuntu, macOS und BSD

```bash
unzip access-manager-generic.zip
cd access-manager
python3 setup.py
```

Alternativ unter Unix:

```bash
./setup.sh
```

### Windows

ZIP entpacken, PowerShell oder Eingabeaufforderung im Ordner öffnen und ausführen:

```powershell
py -3 setup.py
```

Alternativ:

```powershell
.\setup.ps1
```

oder:

```bat
setup.bat
```

## Verhalten des Setups

Das Setup ermittelt seinen eigenen Projektordner. Deshalb kann der Ordner überall liegen und auch später unter einem anderen Pfad entpackt werden. Es erstellt ausschließlich innerhalb dieses Ordners:

- `.venv` für Projektabhängigkeiten
- `.env` für lokale Konfiguration und ein zufälliges Secret
- `data/access.sqlite3` als Produktivdatenbank
- Log- und PID-Dateien beim Start

Es verwendet weder APT, Homebrew, Chocolatey noch globale `pip`-Installationen. Vorhandene nginx-, Apache-, IIS-, Caddy- oder andere Webserver-Konfigurationen werden nicht gelesen oder verändert.

Das Setup fragt Bind-Adresse und Port ab. Standard ist `127.0.0.1:8765`. Nur Ports 1024 bis 65535 sind erlaubt. Vor dem Speichern wird geprüft, ob der Port auf der gewählten Adresse frei ist. Bereits verwendete Ports werden nicht übernommen und vorhandene Prozesse werden niemals beendet.

Für Cloudflare Tunnel sollte die Bind-Adresse `127.0.0.1` bleiben und der Tunnel auf `http://127.0.0.1:8765` zeigen.

## Start und Verwaltung

Nach dem Setup zeigt das Programm den genauen Python-Pfad an. Universell funktioniert:

```bash
.venv/bin/python run.py start
```

Unter Windows:

```powershell
.venv\Scripts\python.exe run.py start
```

Weitere Aktionen:

```text
run.py status
run.py logs
run.py restart
run.py stop
run.py foreground
```

`foreground` ist für Container, Prozessmanager und Fehlersuche gedacht. `start` startet einen Hintergrundprozess im Benutzerkontext und verändert keine Systemdienste.

## Daten und Git

`data/empty.sqlite3` enthält nur die leere Struktur und kann in Git liegen. Folgende Dateien sind durch `.gitignore` ausgeschlossen:

- `.env`
- `.venv/`
- `data/access.sqlite3`
- Logs und PID-Dateien

Vor Updates sollte `data/access.sqlite3` gesichert werden. Das Setup überschreibt eine vorhandene Produktivdatenbank nicht. Eine vorhandene `.env` wird vor einer erneuten Einrichtung gesichert.

## Sicherheit

- Nicht als root oder Administrator erforderlich.
- Standardmäßig nur auf `127.0.0.1` erreichbar.
- Keine privilegierten Ports unter 1024.
- Zufälliges Anwendungssecret.
- Lokale virtuelle Python-Umgebung.
- SQLite-Datei bleibt außerhalb von Git.
- Für öffentlichen Zugriff HTTPS über einen Reverse Proxy oder Cloudflare Tunnel verwenden.

## Einschränkung

Ein Hintergrundstart über `run.py start` ist kein systemweiter Boot-Autostart. Für Boot-Autostart sollte der jeweilige Betreiber später bewusst seinen vorhandenen Prozessmanager verwenden, zum Beispiel systemd, launchd, Windows Task Scheduler, Docker oder einen Hosting-Dienst. Das Projekt trägt sich absichtlich nicht automatisch in das Betriebssystem ein.

# SSO Access Manager

## Ein Kommando auf jedem System

Voraussetzung: Python 3.11 oder neuer ist installiert und als `python` aufrufbar.

Diesen einen Befehl unter Linux, macOS, Windows PowerShell und Windows Terminal ausführen:

```text
python -c "import urllib.request;exec(urllib.request.urlopen('https://raw.githubusercontent.com/florianthepro/sso-access-manager/main/bootstrap.py').read())"
```

Der Befehl lädt `bootstrap.py` nur mit der Python-Standardbibliothek. Danach läuft überall dieselbe OOBE:

1. Installationsordner wählen. Standard ist `/ssoac` unter Unix und `%USERPROFILE%\ssoac` unter Windows.
2. Wenn der Ordner existiert, Reset ausdrücklich bestätigen oder sicher abbrechen.
3. Vor einem Reset optional die SQLite-Datenbank sichern.
4. Repository vollständig herunterladen und installieren.
5. Lokale `.venv` erzeugen.
6. Abhängigkeiten ausschließlich in `.venv` installieren.
7. Bind-IP und freien Port auswählen.
8. Zufälliges Secret und lokale Konfiguration erzeugen.
9. Anwendung optional sofort starten.

Es gibt keinen betriebssystemspezifischen Unterordner und keinen zweiten Installationsweg, der für die normale Nutzung benötigt wird.

## Sicherheitsverhalten

- Keine globale Paketinstallation.
- Keine Änderung an nginx, Apache, IIS, Caddy, Firewall oder vorhandenen Diensten.
- Keine Ports unter 1024.
- Belegte Ports werden durch einen echten Bind-Test abgelehnt.
- Eine vorhandene Installation wird nie ohne ausdrückliche Zustimmung gelöscht.
- Vor einem Reset wird standardmäßig ein Datenbankbackup angeboten.
- Unter Unix wird `sudo` nur verwendet, wenn der gewählte Zielordner ohne erhöhte Rechte nicht geschrieben werden kann.
- Die Anwendung selbst läuft als normaler Benutzer.

## Betrieb nach dem Setup

Die OOBE zeigt den passenden Befehl an. Plattformneutral kann im Installationsordner das Python aus `.venv` verwendet werden:

```text
python run.py start
python run.py status
python run.py logs
python run.py restart
python run.py stop
```

Wenn `python` nicht automatisch auf `.venv` zeigt, unter Unix `.venv/bin/python` und unter Windows `.venv\Scripts\python.exe` verwenden.

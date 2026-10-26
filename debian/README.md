
## Debian OOBE-Installation ohne Systempakete

Das Projekt bringt `setup.sh`, `manage.sh` und `uninstall.sh` mit. `setup.sh` muss als normaler Benutzer ausgeführt werden. Es lädt eine private, portable Python-Laufzeit in `.runtime/`, erstellt `.venv/` im Projektordner und verändert weder APT noch vorhandene Python-, nginx-, Apache- oder andere Webserver-Installationen.

```bash
[ -d /ssoac ] && [ "$(find /ssoac -mindepth 1 -print -quit)" ] && sudo rm -rf /ssoac && sudo mkdir /ssoac && cd /ssoac && chmod a+w . && wget https://github.com/florianthepro/sso-access-manager/archive/refs/heads/main.zip -O sso-access-manager.zip && unzip sso-access-manager.zip && rm sso-access-manager.zip && cd sso-access-manager-main/debian && mv -- * ../../ && cd ../../ && rm -r sso-access-manager-main && chmod +x setup.sh && ./setup.sh
```

Der Assistent fragt Bind-Adresse und Port ab. Standard ist `127.0.0.1:8765`. Nur Ports von 1024 bis 65535 werden akzeptiert. Vor dem Speichern wird geprüft, ob die Adresse wirklich gebunden werden kann. Eine vorhandene `.env` wird gesichert und eine vorhandene Produktivdatenbank nicht überschrieben.

Verwaltung:

```bash
./manage.sh start
./manage.sh status
./manage.sh logs
./manage.sh restart
./manage.sh stop
```

Der Start erfolgt ohne Root-Rechte als Prozess des aktuellen Benutzers. Andere Webserver und deren Ports werden nicht verändert. Für Cloudflare Tunnel sollte die Anwendung auf `127.0.0.1` gebunden bleiben. `cloudflared` kann dann auf `http://127.0.0.1:8765` zeigen.

Das einfache `manage.sh start` überlebt normale SSH-Abmeldungen üblicherweise mit `nohup`, ist aber kein garantierter Boot-Autostart. Ein systemd-User-Service mit Lingering wäre eine optionale spätere Erweiterung und benötigt je nach Debian-Konfiguration eine einmalige Freigabe durch einen Administrator.

Deinstallation der ausschließlich privaten Laufzeit:

```bash
./uninstall.sh
```

Dabei wird gefragt, ob Konfiguration und Datenbank ebenfalls gelöscht werden sollen.

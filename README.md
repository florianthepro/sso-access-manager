# SSO Access Manager

## Installation

Linux:

```bash
python3 -c "import urllib.request;exec(urllib.request.urlopen('https://raw.githubusercontent.com/florianthepro/sso-access-manager/main/bootstrap.py').read())"
```

macOS:

```bash
python3 -c "import urllib.request;exec(urllib.request.urlopen('https://raw.githubusercontent.com/florianthepro/sso-access-manager/main/bootstrap.py').read())"
```

Windows:

```powershell
py -3 -c "import urllib.request;exec(urllib.request.urlopen('https://raw.githubusercontent.com/florianthepro/sso-access-manager/main/bootstrap.py').read())"
```

Nicht mit `sudo` starten. Falls `/ssoac` Root gehoert, fordert das Bootstrap-Skript sudo nur fuer das Entfernen beziehungsweise Anlegen dieses Ordners an und gibt ihn danach an den aktuellen Benutzer zurueck.

Wenn ein Port belegt ist, wird nichts beendet. Das Setup nennt automatisch einen freien Portvorschlag und fragt erneut.

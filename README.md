# SSO Access Manager

Linux/macOS:

```bash
python3 -c "import urllib.request;exec(urllib.request.urlopen('https://raw.githubusercontent.com/florianthepro/sso-access-manager/main/bootstrap.py').read())"
```

Windows:

```powershell
py -3 -c "import urllib.request;exec(urllib.request.urlopen('https://raw.githubusercontent.com/florianthepro/sso-access-manager/main/bootstrap.py').read())"
```

Nicht mit sudo starten. Das Setup installiert nur in `.venv`, prueft IP und Port, erzeugt ein Secret und legt SQLite lokal an.

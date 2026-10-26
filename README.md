# SSO Access Manager v3

Ein-Kommando-OOBE:

```text
python -c "import urllib.request;exec(urllib.request.urlopen('https://raw.githubusercontent.com/florianthepro/sso-access-manager/main/bootstrap.py').read())"
```

## Datenmodell

- Erster Nutzer: nur Benutzername plus Passkey oder Passwort+TOTP.
- Profildaten werden anschließend gepflegt.
- `profile_fields` bestimmt für reguläre und Gastkonten je Feld `HIDDEN`, `OPTIONAL` oder `REQUIRED`.
- `show_optional_during_registration` steuert, ob optionale Felder bereits bei der Registrierung angezeigt werden.
- Systeme besitzen `domain`, `allowed_origin`, Zertifikatsmodus sowie optional mTLS-Fingerprint und API-Key-Hash.
- Ein gültiges Serverzertifikat allein authentifiziert kein aufrufendes System. API-Zugriff benötigt zusätzlich mTLS oder ein anderes System-Credential.
- `system_user_fields` legt pro System und Nutzer fest, welche Profilfelder herausgegeben werden dürfen.
- Gruppen, Spaces, Rollen und System-Permissions bleiben über Assignments verbunden.

Die Produktivdatenbank liegt in `data/access.sqlite3`; `data/empty.sqlite3` enthält ausschließlich das Schema.

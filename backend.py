import hashlib,hmac,html,os,re,secrets,sqlite3,uuid
from datetime import datetime,timezone
from pathlib import Path
from fastapi import FastAPI,Form,HTTPException,Request
from fastapi.responses import HTMLResponse,RedirectResponse
from pwdlib import PasswordHash
B=Path(__file__).resolve().parent; DB=Path(os.getenv('DATABASE_PATH',B/'data/access.sqlite3')); SECRET=os.environ['APP_SECRET']; PH=PasswordHash.recommended(); app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
def now():return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def uid(p):return p+'_'+uuid.uuid4().hex
def db():c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;c.execute('pragma foreign_keys=on');c.execute('pragma busy_timeout=5000');return c
def page(body,status=200):return HTMLResponse('<!doctype html><html lang=de><meta charset=utf-8><meta name=viewport content="width=device-width"><title>SSO Access Manager</title><style>body{font:16px system-ui;max-width:760px;margin:3rem auto;padding:1rem;background:#eef2f6}main{background:white;padding:1.5rem;border-radius:12px}form{display:grid;gap:.8rem}input,select,button{font:inherit;padding:.7rem}button{background:#1769aa;color:white;border:0}small{color:#555}</style><main>'+body+'</main></html>',status)
def initialized():
 c=db();r=c.execute('select setup_completed from app_settings where id=1').fetchone();c.close();return bool(r and r[0])
@app.exception_handler(Exception)
async def error(request,exc):
 if isinstance(exc,HTTPException):return page(f'<h1>Fehler</h1><p>{html.escape(str(exc.detail))}</p>',exc.status_code)
 return page('<h1>Interner Fehler</h1><p>Details wurden aus Sicherheitsgruenden nur im Serverlog ausgegeben.</p>',500)
@app.get('/')
def home():
 if not initialized():return RedirectResponse('/setup',303)
 c=db();u=c.execute('select username,preferred_auth_method from users order by username').fetchall();s=c.execute('select o.name,systems.domain from systems join objects o on o.id=systems.id').fetchall();c.close()
 return page('<h1>SSO Access Manager</h1><h2>Nutzer</h2><ul>'+''.join(f'<li>{html.escape(x[0])} ({x[1]})</li>' for x in u)+'</ul><h2>Systeme</h2><ul>'+''.join(f'<li>{html.escape(x[0])}: {html.escape(x[1])}</li>' for x in s)+'</ul>')
@app.get('/setup')
def setup_get():
 if initialized():return RedirectResponse('/',303)
 return page('''<h1>Ersteinrichtung</h1><p>Der erste Nutzer braucht nur Benutzername und eine starke Anmeldemethode. Profildaten werden spaeter gepflegt.</p><form method=post><label>Instanzname<input name=instance maxlength=100 required></label><label>Benutzername<input name=username pattern="[A-Za-z0-9._-]{3,50}" required></label><label>Anmeldung<select name=auth_method><option value=PASSKEY>Passkey</option><option value=PASSWORD_MFA>Passwort + TOTP</option></select></label><label>Passwort fuer Passwort + TOTP<input name=password type=password minlength=12 maxlength=128></label><label>TOTP-Secret fuer Passwort + TOTP<input name=totp_secret minlength=16 maxlength=128></label><small>Passkey wird im naechsten Schritt registriert. Die Grunddatenbank speichert die WebAuthn-Credentials getrennt.</small><button>Einrichten</button></form>''')
@app.post('/setup')
def setup_post(instance:str=Form(...,min_length=1,max_length=100),username:str=Form(...,min_length=3,max_length=50),auth_method:str=Form(...),password:str=Form(''),totp_secret:str=Form('')):
 if initialized():return RedirectResponse('/',303)
 if not re.fullmatch(r'[A-Za-z0-9._-]{3,50}',username):raise HTTPException(422,'Ungueltiger Benutzername')
 if auth_method not in {'PASSKEY','PASSWORD_MFA'}:raise HTTPException(422,'Ungueltige Anmeldemethode')
 if auth_method=='PASSWORD_MFA' and (len(password)<12 or len(totp_secret)<16):raise HTTPException(422,'Passwort mit mindestens 12 Zeichen und TOTP-Secret sind Pflicht')
 t=now();u=uid('usr');c=db()
 try:
  c.execute('begin immediate')
  if c.execute('select 1 from app_settings where id=1').fetchone():raise HTTPException(409,'Setup wurde bereits abgeschlossen')
  c.execute('insert into app_settings values(1,1,?,?,?,?,?)',(instance.strip(),'OWNER_ONLY','CLOSED',t,t))
  c.execute('insert into objects values(?,?,?,?,?,?,?,?,?)',(u,'USER',None,username,None,None,None,t,t))
  c.execute('insert into users values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(u,'REGULAR',username,None,None,None,None,None,PH.hash(password) if password else None,totp_secret if totp_secret else None,1 if auth_method=='PASSWORD_MFA' else 0,auth_method,t,t))
  defaults=[('email','E-Mail','EMAIL'),('first_name','Vorname','TEXT'),('last_name','Nachname','TEXT'),('date_of_birth','Geburtsdatum','DATE'),('fsk_limit','FSK','INTEGER')]
  for i,(k,l,d) in enumerate(defaults):c.execute('insert into profile_fields values(?,?,?,?,?,?,?,?,?,?)',(uid('fld'),k,l,d,'OPTIONAL','OPTIONAL',0,254 if d in('TEXT','EMAIL') else None,i,t,t))
  c.commit()
 except Exception:c.rollback();raise
 finally:c.close()
 return RedirectResponse('/setup/passkey' if auth_method=='PASSKEY' else '/',303)
@app.get('/setup/passkey')
def passkey_info():return page('<h1>Passkey-Einrichtung</h1><p>Die Datenbank ist vorbereitet. Die vollstaendige WebAuthn-Challenge- und Signaturpruefung muss als naechster Authentifizierungsbaustein aktiviert werden. Bis dahin ist kein unsicherer Schein-Passkey gespeichert worden.</p><a href="/">Weiter</a>')

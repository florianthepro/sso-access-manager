import base64,hashlib,hmac,html,io,json,os,re,secrets,sqlite3,uuid
from datetime import datetime,timedelta,timezone
from pathlib import Path
from fastapi import FastAPI,Form,HTTPException,Request
from fastapi.responses import HTMLResponse,JSONResponse,RedirectResponse,Response
from pwdlib import PasswordHash
import pyotp,qrcode
B=Path(__file__).resolve().parent;DB=Path(os.environ['DATABASE_PATH']);SECRET=os.environ['APP_SECRET'].encode();PH=PasswordHash.recommended();app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
def now():return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def uid(p):return p+'_'+uuid.uuid4().hex
def con():c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;c.execute('pragma foreign_keys=on');return c
def enc(v):
 b=v.encode();k=hashlib.sha256(SECRET).digest();return base64.urlsafe_b64encode(bytes(x^k[i%len(k)] for i,x in enumerate(b))).decode()
def dec(v):
 b=base64.urlsafe_b64decode(v);k=hashlib.sha256(SECRET).digest();return bytes(x^k[i%len(k)] for i,x in enumerate(b)).decode()
def page(x,s=200):return HTMLResponse('<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width"><style>body{font:16px system-ui;max-width:800px;margin:3rem auto;padding:1rem;background:#eef}main{background:white;padding:1.5rem;border-radius:12px}form{display:grid;gap:.7rem}input,select,button{padding:.7rem;font:inherit}</style><main>'+x+'</main>',s)
def initialized():c=con();r=c.execute('select 1 from settings').fetchone();c.close();return bool(r)
@app.middleware('http')
async def headers(req,call):
 try:r=await call(req)
 except Exception as e:
  print('ERROR',repr(e),flush=True);r=page('<h1>Fehler</h1><p>Siehe Serverlog.</p>',500)
 r.headers['X-Content-Type-Options']='nosniff';r.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'";return r
@app.get('/')
def home():
 if not initialized():return RedirectResponse('/setup',303)
 c=con();u=c.execute('select username,preferred_auth from users').fetchall();c.close();return page('<h1>SSO Access Manager</h1><ul>'+''.join(f'<li>{html.escape(x[0])} ({x[1]})</li>' for x in u)+'</ul>')
@app.get('/setup')
def setup_get():
 if initialized():return RedirectResponse('/',303)
 return page('''<h1>Setup</h1><form method=post><input name=instance placeholder=Instanzname required maxlength=100><input name=username placeholder=Benutzername required pattern="[A-Za-z0-9._-]{3,50}"><select name=method><option value=PASSWORD_TOTP>Passwort + TOTP</option><option value=PASSKEY>Passkey</option></select><input name=password type=password minlength=12 maxlength=128 placeholder="Passwort (bei TOTP)"><button>Weiter</button></form>''')
@app.post('/setup')
def setup_post(instance:str=Form(...),username:str=Form(...),method:str=Form(...),password:str=Form('')):
 if initialized():return RedirectResponse('/',303)
 if not re.fullmatch(r'[A-Za-z0-9._-]{3,50}',username):raise HTTPException(422,'Benutzername ungueltig')
 if method=='PASSKEY' and not os.environ.get('RP_ID'):return page('<h1>Passkey braucht HTTPS</h1><p>APP_ORIGIN/RP_ID im Host-Setup setzen.</p>',422)
 if method=='PASSWORD_TOTP' and len(password)<12:return page('<h1>Passwort zu kurz</h1>',422)
 t=now();u=uid('usr');secret=pyotp.random_base32() if method=='PASSWORD_TOTP' else None;c=con()
 try:
  c.execute('begin immediate');c.execute('insert into settings values(1,?,?,?,?,?)',(instance,'CLOSED',t,t));c.execute('insert into objects values(?,?,?,?,?,?,?,?,?)',(u,'USER',None,username,None,None,None,t,t));c.execute('insert into users values(?,?,?,?,?,?,?,?,?,?)',(u,'REGULAR',username,PH.hash(password) if password else None,enc(secret) if secret else None,0,method,t,t));c.commit()
 finally:c.close()
 return RedirectResponse('/setup/totp' if secret else '/setup/passkey',303)
@app.get('/setup/totp')
def totp_page():
 c=con();u=c.execute("select username,totp_secret_enc from users where preferred_auth='PASSWORD_TOTP' and mfa_enabled=0 order by created_at limit 1").fetchone();c.close()
 if not u:return RedirectResponse('/',303)
 uri=pyotp.TOTP(dec(u[1])).provisioning_uri(u[0],issuer_name='SSO Access Manager')
 return page(f'<h1>TOTP aktivieren</h1><img src="/setup/totp/qr"><form method=post><input name=code pattern="[0-9]{{6}}" required><button>Bestaetigen</button></form><small>{html.escape(uri)}</small>')
@app.get('/setup/totp/qr')
def qr():
 c=con();u=c.execute("select username,totp_secret_enc from users where mfa_enabled=0 limit 1").fetchone();c.close();uri=pyotp.TOTP(dec(u[1])).provisioning_uri(u[0],issuer_name='SSO Access Manager');im=qrcode.make(uri);b=io.BytesIO();im.save(b,'PNG');return Response(b.getvalue(),media_type='image/png')
@app.post('/setup/totp')
def totp_verify(code:str=Form(...)):
 c=con();u=c.execute("select id,totp_secret_enc from users where mfa_enabled=0 limit 1").fetchone()
 if not u or not pyotp.TOTP(dec(u[1])).verify(code,valid_window=1):c.close();return page('<h1>Code ungueltig</h1><a href=/setup/totp>Zurueck</a>',422)
 c.execute('update users set mfa_enabled=1 where id=?',(u[0],));c.commit();c.close();return RedirectResponse('/',303)
@app.get('/setup/passkey')
def passkey():return page('<h1>Passkey</h1><p>WebAuthn ist im Schema vorbereitet. Die finale Aktivierung erfordert die konfigurierte HTTPS-Origin.</p>')

import base64,hashlib,hmac,html,io,json,os,re,secrets,sqlite3,uuid
from datetime import datetime,timedelta,timezone
from pathlib import Path
from fastapi import FastAPI,Form,HTTPException,Request
from fastapi.responses import HTMLResponse,JSONResponse,RedirectResponse,Response
from pwdlib import PasswordHash
from cryptography.fernet import Fernet
import pyotp,qrcode
B=Path(__file__).resolve().parent; DB=Path(os.environ['DATABASE_PATH']); SECRET=os.environ['APP_SECRET']; PH=PasswordHash.recommended(); F=Fernet(base64.urlsafe_b64encode(hashlib.sha256(SECRET.encode()).digest())); app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
def now():return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def uid(p):return p+'_'+uuid.uuid4().hex
def db():c=sqlite3.connect(DB,timeout=5);c.row_factory=sqlite3.Row;c.execute('pragma foreign_keys=on');c.execute('pragma busy_timeout=5000');return c
def token_hash(v):return hmac.new(SECRET.encode(),v.encode(),hashlib.sha256).hexdigest()
def page(title,body,status=200):return HTMLResponse(f'<!doctype html><html lang=de><meta charset=utf-8><meta name=viewport content="width=device-width"><title>{html.escape(title)}</title><link rel=stylesheet href=/static/style.css><main><h1>{html.escape(title)}</h1>{body}</main></html>',status)
def initialized():c=db();r=c.execute('select 1 from settings').fetchone();c.close();return bool(r)
def current(req):
 t=req.cookies.get('session');
 if not t:return None
 c=db();r=c.execute('select s.*,u.username from sessions s join users u on u.id=s.user_id where token_hash=? and expires_at>?',(token_hash(t),now())).fetchone();c.close();return dict(r) if r else None
def require(req):
 u=current(req)
 if not u:raise HTTPException(401,'Anmeldung erforderlich')
 return u
def form_input(name,label,typ='text',required=False):return f'<label>{html.escape(label)}<input name={name} type={typ} maxlength=255 {"required" if required else ""}></label>'
@app.middleware('http')
async def secure(req,call):
 try:r=await call(req)
 except HTTPException as e:r=page('Fehler',html.escape(str(e.detail)),e.status_code)
 except Exception as e:print('ERROR',repr(e),flush=True);r=page('Fehler','Interner Fehler. Details im Serverlog.',500)
 r.headers.update({'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"});return r
@app.get('/')
def home(req:Request):
 if not initialized():return RedirectResponse('/setup',303)
 u=current(req)
 if not u:return RedirectResponse('/login',303)
 return page('SSO Access Manager',f'<p>Angemeldet als <b>{html.escape(u["username"])}</b></p><nav><a href=/admin>Verwaltung</a> · <a href=/logout>Abmelden</a></nav>')
@app.get('/setup')
def setup_get():
 if initialized():return RedirectResponse('/',303)
 return page('Ersteinrichtung','<form method=post>'+form_input('instance','Instanzname',required=True)+form_input('username','Benutzername',required=True)+'<label>Methode<select name=method><option value=PASSWORD_TOTP>Passwort + TOTP</option><option value=PASSKEY>Passkey</option></select></label>'+form_input('password','Passwort','password')+'<button>Weiter</button></form>')
@app.post('/setup')
def setup_post(instance:str=Form(...,max_length=100),username:str=Form(...,max_length=50),method:str=Form(...),password:str=Form('',max_length=128)):
 if initialized():return RedirectResponse('/',303)
 if not re.fullmatch(r'[A-Za-z0-9._-]{3,50}',username):return page('Fehler','Benutzername ungueltig',422)
 if method=='PASSKEY':return page('Passkey','Passkey ist nur ueber eine konfigurierte HTTPS-Origin aktivierbar. Waehle bis dahin Passwort + TOTP.',422)
 if len(password)<12:return page('Fehler','Passwort muss mindestens 12 Zeichen haben.',422)
 t=now();u=uid('usr');secret=pyotp.random_base32();c=db()
 try:
  c.execute('begin immediate');c.execute('insert into settings values(1,?,?,?,?,?)',(instance.strip(),'CLOSED',t,t));c.execute('insert into objects values(?,?,?,?,?,?,?,?,?)',(u,'USER',None,username,None,None,None,t,t));c.execute('insert into users values(?,?,?,?,?,?,?,?,?,?)',(u,'REGULAR',username,PH.hash(password),F.encrypt(secret.encode()).decode(),0,'PASSWORD_TOTP',0,t,t));
  defaults=[('email','E-Mail','EMAIL'),('first_name','Vorname','TEXT'),('last_name','Nachname','TEXT'),('date_of_birth','Geburtsdatum','DATE'),('fsk_limit','FSK','INTEGER')]
  for i,(k,l,d) in enumerate(defaults):c.execute('insert into profile_fields values(?,?,?,?,?,?,?,?,?)',(uid('fld'),k,l,d,'OPTIONAL','OPTIONAL',0,254,i))
  c.commit()
 except: c.rollback();raise
 finally:c.close()
 return RedirectResponse('/setup/totp',303)
@app.get('/setup/totp')
def totp_get():
 c=db();u=c.execute('select username,totp_secret from users where setup_complete=0 limit 1').fetchone();c.close()
 if not u:return RedirectResponse('/',303)
 secret=F.decrypt(u['totp_secret'].encode()).decode();uri=pyotp.TOTP(secret).provisioning_uri(u['username'],issuer_name='SSO Access Manager')
 return page('TOTP aktivieren','<img alt="QR-Code" src=/setup/totp/qr><form method=post>'+form_input('code','6-stelliger Code',required=True)+'<button>Bestaetigen</button></form>')
@app.get('/setup/totp/qr')
def totp_qr():
 c=db();u=c.execute('select username,totp_secret from users where setup_complete=0 limit 1').fetchone();c.close()
 if not u:raise HTTPException(404)
 uri=pyotp.TOTP(F.decrypt(u['totp_secret'].encode()).decode()).provisioning_uri(u['username'],issuer_name='SSO Access Manager');im=qrcode.make(uri);b=io.BytesIO();im.save(b,'PNG');return Response(b.getvalue(),media_type='image/png')
@app.post('/setup/totp')
def totp_post(code:str=Form(...,min_length=6,max_length=6)):
 c=db();u=c.execute('select id,totp_secret from users where setup_complete=0 limit 1').fetchone()
 if not u or not pyotp.TOTP(F.decrypt(u['totp_secret'].encode()).decode()).verify(code,valid_window=1):c.close();return page('Fehler','Code ungueltig.','<a href=/setup/totp>Zurueck</a>' if False else 422)
 c.execute('update users set mfa_enabled=1,setup_complete=1 where id=?',(u['id'],));c.commit();c.close();return RedirectResponse('/login',303)
@app.get('/login')
def login_get():return page('Anmeldung','<form method=post>'+form_input('username','Benutzername',required=True)+form_input('password','Passwort','password',True)+form_input('totp','TOTP-Code',required=True)+'<button>Anmelden</button></form>')
@app.post('/login')
def login_post(username:str=Form(...),password:str=Form(...),totp:str=Form(...)):
 c=db();u=c.execute('select * from users where username=? collate nocase and setup_complete=1',(username,)).fetchone()
 ok=bool(u and u['password_hash'] and PH.verify(password,u['password_hash']) and pyotp.TOTP(F.decrypt(u['totp_secret'].encode()).decode()).verify(totp,valid_window=1))
 if not ok:c.close();return page('Anmeldung','Anmeldung fehlgeschlagen.',401)
 raw=secrets.token_urlsafe(48);t=now();exp=(datetime.now(timezone.utc)+timedelta(hours=12)).replace(microsecond=0).isoformat();c.execute('insert into sessions values(?,?,?,?,?,?)',(uid('ses'),u['id'],token_hash(raw),secrets.token_urlsafe(24),exp,t));c.commit();c.close();r=RedirectResponse('/',303);r.set_cookie('session',raw,httponly=True,secure=os.getenv('COOKIE_SECURE')=='true',samesite='strict',max_age=43200);return r
@app.get('/logout')
def logout(req:Request):
 t=req.cookies.get('session');c=db();c.execute('delete from sessions where token_hash=?',(token_hash(t or ''),));c.commit();c.close();r=RedirectResponse('/login',303);r.delete_cookie('session');return r
@app.get('/admin')
def admin(req:Request):
 u=require(req);c=db();objs=c.execute("select id,type,name,status from objects where type<>'USER' order by type,name").fetchall();systems=c.execute('select o.name,s.domain from systems s join objects o on o.id=s.id').fetchall();c.close();return page('Verwaltung','<h2>Objekte</h2><ul>'+''.join(f'<li>{html.escape(x[1])}: {html.escape(x[2])}</li>' for x in objs)+'</ul><h2>Systeme</h2><ul>'+''.join(f'<li>{html.escape(x[0])}: {html.escape(x[1])}</li>' for x in systems)+'</ul><p>Die sichere Datenstruktur fuer Felder, Freigaben, Assignments, Einladungen, Systeme und Permissions ist aktiv.</p>')
@app.get('/api/system/user/{user_id}')
def system_user(user_id:str,request:Request):
 key=request.headers.get('Authorization','').removeprefix('Bearer ').strip();origin=request.headers.get('Origin','');c=db();systems=c.execute('select * from systems where allowed_origin=?',(origin,)).fetchall();system=next((s for s in systems if hmac.compare_digest(s['api_key_hash'],token_hash(key))),None)
 if not system:c.close();raise HTTPException(401,'System nicht autorisiert')
 grants={r['data_key'] for r in c.execute('select data_key from data_grants where system_id=? and user_id=? and allowed=1',(system['id'],user_id))};user=c.execute('select username from users where id=?',(user_id,)).fetchone();out={'user_id':user_id}
 if user and 'username' in grants:out['username']=user['username']
 if 'permissions' in grants:out['permissions']=[r['name'] for r in c.execute("select p.name from assignments a join permissions p on p.id=a.permission_id where a.source_id=? and p.system_id=? and a.state='ACCEPTED'",(user_id,system['id']))]
 c.close();return out

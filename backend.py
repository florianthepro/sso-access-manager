import os,sqlite3,secrets,hashlib,hmac
from pathlib import Path
from fastapi import FastAPI,Request,Form
from fastapi.responses import HTMLResponse,RedirectResponse
from pwdlib import PasswordHash
B=Path(__file__).parent; DB=Path(os.getenv('DATABASE_PATH',B/'data/access.sqlite3')); S=os.environ['APP_SECRET']; ph=PasswordHash.recommended(); app=FastAPI(docs_url=None,redoc_url=None)
def con(): c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;c.execute('pragma foreign_keys=on');return c
def page(body): return HTMLResponse('<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width"><title>Access Manager</title><style>body{font:16px system-ui;max-width:760px;margin:4rem auto;padding:1rem}form{display:grid;gap:.7rem}input,select,button{padding:.7rem}button{background:#1769aa;color:white;border:0}</style>'+body)
@app.get('/')
def home(request:Request):
 c=con(); setup=c.execute('select count(*) from app_settings').fetchone()[0]; users=c.execute('select username,first_name,last_name,account_kind,fsk_limit from users').fetchall(); c.close()
 if not setup:return RedirectResponse('/setup')
 return page('<h1>Access Manager</h1><p>Grundsystem läuft.</p><h2>Nutzer</h2><ul>'+''.join(f'<li>{u[0]}: {u[1]} {u[2]} ({u[3]}, FSK {u[4]})</li>' for u in users)+'</ul>')
@app.get('/setup')
def setup_form(): return page('<h1>Ersteinrichtung</h1><form method=post><input name=instance placeholder=Instanzname maxlength=100 required><input name=username placeholder=Benutzername pattern="[A-Za-z0-9._-]{3,50}" required><input name=email type=email placeholder=E-Mail required><input name=first placeholder=Vorname maxlength=100 required><input name=last placeholder=Nachname maxlength=100 required><input name=password type=password minlength=12 maxlength=128 placeholder=Passwort required><button>Einrichten</button></form>')
@app.post('/setup')
def setup(instance:str=Form(...,max_length=100),username:str=Form(...,min_length=3,max_length=50),email:str=Form(...,max_length=254),first:str=Form(...,max_length=100),last:str=Form(...,max_length=100),password:str=Form(...,min_length=12,max_length=128)):
 c=con(); t='2026-10-26T00:00:00+00:00'
 if c.execute('select count(*) from app_settings').fetchone()[0]: c.close(); return RedirectResponse('/',303)
 uid='usr_'+secrets.token_hex(16); c.execute('insert into objects values(?,?,?,?,?,?,?,?,?)',(uid,'USER',None,(first+' '+last).strip(),None,None,None,t,t)); c.execute('insert into users values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(uid,'REGULAR',username,email,first,last,None,18,ph.hash(password),None,0,'PASSWORD','{}',t,t)); c.execute('insert into app_settings values(1,1,?,?,?,?,?,?,?,?,?,?,?,?)',(instance,'OWNER_ONLY','CLOSED',1,1,0,0,0,1,t,t)); c.commit();c.close();return RedirectResponse('/',303)

import os,signal,subprocess,sys,time
from pathlib import Path
B=Path(__file__).resolve().parent;P=B/'data/app.pid';L=B/'data/app.log'
for line in (B/'.env').read_text().splitlines():
 if '=' in line:k,v=line.split('=',1);os.environ[k]=v
def alive(p):
 try:os.kill(p,0);return True
 except:return False
def pid():
 try:return int(P.read_text())
 except:return 0
a=sys.argv[1] if len(sys.argv)>1 else 'status'
if a=='start':
 if alive(pid()):print('Laeuft bereits');raise SystemExit
 f=L.open('a');q=subprocess.Popen([sys.executable,'-m','uvicorn','backend:app','--host',os.environ['BIND_HOST'],'--port',os.environ['BIND_PORT'],'--workers','1'],cwd=B,stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=os.name!='nt');P.write_text(str(q.pid));time.sleep(1);print('Gestartet' if alive(q.pid) else f'Fehler, siehe {L}')
elif a=='stop':
 p=pid();
 if alive(p):os.kill(p,signal.SIGTERM)
 P.unlink(missing_ok=True);print('Gestoppt')
elif a=='restart':subprocess.run([sys.executable,__file__,'stop']);subprocess.run([sys.executable,__file__,'start'])
elif a=='status':print(f'Laeuft PID {pid()}' if alive(pid()) else 'Gestoppt')
elif a=='logs':print(L.read_text(errors='replace')[-20000:] if L.exists() else 'Keine Logs')

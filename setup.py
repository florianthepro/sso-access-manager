import os,secrets,shutil,socket,subprocess,sys
from pathlib import Path
B=Path(__file__).resolve().parent;V=B/'.venv';D=B/'data';E=B/'.env'
def ask(p,d):
 v=input(f'{p} [{d}]: ').strip();return v or d
def main():
 if sys.version_info<(3,11):raise SystemExit('Python 3.11+ erforderlich')
 if not V.exists():subprocess.run([sys.executable,'-m','venv',str(V)],check=True)
 py=V/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
 subprocess.run([str(py),'-m','pip','install','--disable-pip-version-check','-q','-r',str(B/'requirements.txt')],check=True)
 host=ask('IP','127.0.0.1')
 while True:
  port=int(ask('Port','8765'))
  if not 1024<=port<=65535:print('Port 1024-65535 erforderlich');continue
  s=socket.socket(socket.AF_INET6 if ':' in host else socket.AF_INET)
  try:s.bind((host,port));s.close();break
  except OSError:
   s.close()
   probe=socket.socket(socket.AF_INET6 if ':' in host else socket.AF_INET);probe.bind((host,0));suggested=probe.getsockname()[1];probe.close()
   print(f'Port {port} belegt. Vorschlag: {suggested}')
 origin=ask('Oeffentliche HTTPS-Origin fuer Passkeys (leer = lokal ohne Passkey)','')
 rp_id=''
 if origin:
  from urllib.parse import urlparse
  u=urlparse(origin); 
  if u.scheme!='https' or not u.hostname:raise SystemExit('Origin muss https://domain sein')
  rp_id=u.hostname
 vals={'APP_SECRET':secrets.token_urlsafe(48),'DATABASE_PATH':str((D/'app.sqlite3').resolve()),'BIND_HOST':host,'BIND_PORT':str(port),'APP_ORIGIN':origin,'RP_ID':rp_id,'COOKIE_SECURE':'true' if origin else 'false'}
 E.write_text(''.join(f'{k}={v}\n' for k,v in vals.items()))
 if os.name!='nt':os.chmod(E,0o600)
 if not (D/'app.sqlite3').exists():shutil.copy2(D/'empty.sqlite3',D/'app.sqlite3')
 print(f'Fertig: http://{host}:{port}')
 if input('Starten? [J/n]: ').strip().lower()!='n':os.execv(str(py),[str(py),str(B/'run.py'),'start'])
if __name__=='__main__':main()

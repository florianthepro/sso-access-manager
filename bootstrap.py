import io,os,shutil,subprocess,sys,tempfile,urllib.request,zipfile
from pathlib import Path
URL='https://github.com/florianthepro/sso-access-manager/archive/refs/heads/main.zip';D=Path('/ssoac') if os.name!='nt' else Path.home()/'ssoac'
def run(x):subprocess.run(x,check=True)
if hasattr(os,'geteuid') and os.geteuid()==0:raise SystemExit('Nicht mit sudo starten.')
if D.exists():
 if input(f'{D} ersetzen? [y/N]: ').lower() not in ('y','j','ja','yes'):raise SystemExit('Abbruch')
 try:shutil.rmtree(D)
 except PermissionError:run(['sudo','rm','-rf','--',str(D)])
a=urllib.request.urlopen(URL).read();t=Path(tempfile.mkdtemp());zipfile.ZipFile(io.BytesIO(a)).extractall(t);s=next(t.iterdir())
try:shutil.copytree(s,D)
except PermissionError:run(['sudo','mkdir','-p',str(D)]);run(['sudo','cp','-a',f'{s}/.',str(D)]);run(['sudo','chown','-R',f'{os.getuid()}:{os.getgid()}',str(D)])
os.chdir(D);os.execv(sys.executable,[sys.executable,str(D/'setup.py')])

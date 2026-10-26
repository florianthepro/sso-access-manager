import io,os,shutil,sys,tempfile,urllib.request,zipfile
from pathlib import Path
URL='https://github.com/florianthepro/sso-access-manager/archive/refs/heads/main.zip';D=Path('/ssoac') if os.name!='nt' else Path.home()/'ssoac'
if D.exists():
 if input(f'{D} ersetzen? [y/N]: ').lower() not in ('y','j','ja','yes'):raise SystemExit('Abbruch')
 shutil.rmtree(D)
r=urllib.request.urlopen(URL).read();t=Path(tempfile.mkdtemp());zipfile.ZipFile(io.BytesIO(r)).extractall(t);s=next(t.iterdir());shutil.copytree(s,D);os.chdir(D);os.execv(sys.executable,[sys.executable,str(D/'setup.py')])

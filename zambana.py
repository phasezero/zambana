from pathlib import Path
from dotenv import dotenv_values
import yaml

env = dotenv_values(str(Path(__file__).parent.absolute())+"/.env")

def startup_check():
    from shutil import which
    
    from os import access
    from os import X_OK
    print(Path.cwd())
    check = True
    if which("docker-compose") is None:
        print("Could not find docker-compose. Check your docker installation.")
        check = False
    if not Path(str(Path(__file__).parent.absolute())+"/.env").exists():
        print("Could not find .env - Aborting.")
        check = False
    if not Path(str(Path(__file__).parent.absolute())+"/scripts/backup.sh"):
        print("Could not find scripts/backup.sh - Aborting.")
        check = False
    else:
        if not access(str(Path(__file__).parent.absolute())+"/scripts/backup.sh", X_OK):
            print('scripts/backup.sh not executable... setting to executable')
            import stat
            f=Path(str(Path(__file__).parent.absolute())+"/scripts/backup.sh")
            print(f)
            f.chmod(f.stat().st_mode | stat.S_IEXEC)
    return check

if startup_check() :
    import shlex, subprocess
      
    print("works")
    command_line = f"docker-compose -p {env['PROJECT_NAME']} up -d"
    args = shlex.split(command_line)
    print(args)
    #subprocess.Popen(args)

else:
    print("No")
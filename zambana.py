

def startup_check():
    from os import X_OK, access
    from shutil import which
    print(Path.cwd())
    check = True
    if which("docker-compose") is None:
        print("Could not find docker-compose. Check your docker installation.")
        #check = False
    if not Path(__file__).parent.absolute().joinpath(".env").exists():
        print("Could not find .env - Aborting.")
        check = False
    if not Path(__file__).parent.absolute().joinpath("scripts/backup.sh").exists():
        print("Could not find scripts/backup.sh - Aborting.")
        check = False
    else:
        if not access(Path(__file__).parent.absolute().joinpath("scripts/backup.sh"), X_OK):
            print('scripts/backup.sh not executable... setting to executable')
            import stat
            f=Path(__file__).parent.absolute().joinpath("scripts/backup.sh")
            f.chmod(f.stat().st_mode | stat.S_IEXEC)
    if not Path(__file__).parent.absolute().joinpath("conf/zammad.yml").exists():
        print("Could not find zammad configuration - Aborting.")
        check = False
    '''
    TODO
    if not Path(__file__).parent.absolute().joinpath("conf/elasticsearch.yml").exists():
        print("Could not find elasticsearch configuration - Aborting.")
        check = False
    if not Path(__file__).parent.absolute().joinpath("conf/kibana.yml").exists():
        print("Could not find kibana configuration - Aborting.")
        check = False
    '''
    return check

def docker_install(project_name) :
    import shlex
    
    
    command_line = f"docker-compose -p {project_name} up -d"
    args = shlex.split(command_line)
    #print(args)
    subprocess.call(args)
    return

def zammad_config (env, zammad_conf):
    print (f"\nConfiguring zammad")
    for (k,v) in zammad_conf.items():
        if str(v)[0] == "$":
            v = env[v[1:]]
        if type(v) == bool:
            v = str(v).lower()
        if type(v) == str:
            args = ['docker-compose', '-exec', f'rails r "Settings.set(\'{k}\',\'{v}\')"']
        else: 
            args = ['docker-compose', '-exec', f'rails r "Settings.set(\'{k}\',{v})"']
        subprocess.call(args)


#    while read -r line
#    do
#        varstr=$(echo "$line" | cut -d "'" -f 4 | sed 's/)$//')
#        # needed to check if a value is configured in .env
#        if [[ $varstr =~ ^\$.* ]]; then
#            eval varstr_eval="$varstr"
#            line=${line/$varstr/"$varstr_eval"}
#        fi
        # execute rails in docker container
#        docker exec "$PROJECT_NAME"-zammad-railsserver-1 rails r ""$line""
#        wait $!
#    done < <(grep -v '^#' "$1"/conf/zammad.conf)



    return


   



def main() -> int:

    if startup_check() :
        import yaml
        from dotenv import dotenv_values
        
        env = dotenv_values(str(Path(__file__).parent.absolute())+"/.env")
        with open(Path(__file__).parent.absolute().joinpath("conf/zammad.yml")) as stream:
            zammad_conf = yaml.safe_load(stream)


        docker_install(env["PROJECT_NAME"])
        zammad_config(env,zammad_conf)
        print(f'zammad.conf: \n{zammad_conf}')

    else:
        print("No")
    return 0

if __name__ == '__main__':
    import sys
    import subprocess, shlex
    from pathlib import Path
    sys.exit(main()) 
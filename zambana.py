
def yaml_loader(file):
    import yaml
    with open(file, "r") as stream:
        yaml_load = yaml.safe_load(stream)
    stream.close
    return yaml_load

def yaml_dumper(file, data):
    import yaml
    with open(file, "w") as stream:
        yaml.dump(data, stream, default_flow_style=False,
                  explicit_start=True, allow_unicode=True)
    stream.close

def run(cmd):
    import shlex
    from subprocess import PIPE, Popen
    cmdset = cmd.split('|')
    ret = []
    if len(cmdset) == 1:
        args = shlex.split(cmdset[0])
        # subprocess.check_call(args)
        #with Popen(args, stdout=PIPE, stderr=None, shell=False) as process:
            # process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=None, shell=True)
        ret.append(Popen(args, stdout=PIPE, stderr=None, shell=False).communicate())
    else:
        i = 0
        for command in cmdset:
            if i == 0:
                ret.append(Popen(shlex.split(command), stdout=PIPE, stderr=None, shell=False, text=True))
            else:
                ret.append(Popen(shlex.split(command), stdin=ret[i-1].stdout, stdout=PIPE, stderr=None, shell=False, text=True))
            i += 1
        ret[-1] = ret[-1].communicate()
    return ret[-1]

def startup_check():
    '''

    '''
    from os import X_OK, access
    from shutil import which
    import platform
    print(f"\nChecking dependencies")
    check = True
    # Test if requirements for elasticsearch are met
    if platform.system() == 'Linux':
        output, error = run('sysctl vm.max_map_count')
        if output.decode("utf-8").split(" = ")[1][:-1] != "262144":
            check = False
            print("ERROR: Virtual Memory. You need to check your vm.max_map_count.\nSee https://www.elastic.co/guide/en/elasticsearch/reference/current/vm-max-map-count.html for more information.")
            exit

    if which("docker-compose") is None:
        print("Could not find docker-compose. Check your docker installation.")
        # check = False

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
            f = Path(__file__).parent.absolute().joinpath("scripts/backup.sh")
            f.chmod(f.stat().st_mode | stat.S_IEXEC)

    if not Path(__file__).parent.absolute().joinpath("conf/zammad.yml").exists():
        print("Could not find zammad configuration - Aborting.")
        check = False

    if not Path(__file__).parent.absolute().joinpath("conf/elastic.yml").exists():
        print("Could not find elasticsearch configuration - Aborting.")
        check = False

    if not Path(__file__).parent.absolute().joinpath("conf/kibana.yml").exists():
        print("Could not find kibana configuration - Aborting.")
        check = False

    return check

def get_container_id(name):
    command = 'docker ps --format "{{.ID}} {{.Names}}" | grep "'+name+'" | cut -d " " -f1'
    output, error = run(command)
    if error != None:
        print(f"Container {name} not found: ABORT")
        exit
    return output[:-1]

def docker_install(project_name):
    # installing docker stack
    print(f'\nInitalizing docker stack:')
    command_line = f"docker-compose -p {project_name} up -d"
    run(command_line)
    return

def zammad_config(env):
    print(f"\nConfiguring zammad")
    
    railsContainer = get_container_id('zammad-railsserver')

    # read zammad.yml configuration file
    zammad_conf = yaml_loader(
        Path(__file__).parent.absolute().joinpath("conf/zammad.yml"))
    
    # prepair configuration command for each configuration line
    for (k, v) in zammad_conf.items():
        if str(v)[0] == "$":
            v = env[v[1:]]
        if type(v) == bool:
            v = str(v).lower()
        if type(v) == str:
            line = f"Setting.set('{k}','{v}')"
        else:
            line = f"Setting.set('{k}',{v})"

        # execute configuration
        command_line = f'docker exec {railsContainer} /docker-entrypoint.sh rails r "{line}"'
        print(f"\nSetting {k}: {v}")
        output, error = run(command_line)
        if error != None:
            print(f'{k}couldn not be set - check manually')
        else:
            print(output.decode('utf-8'))
    return 0

def elastic_config(env):
    print(f"\nConfiguring elasticsearch")
    
    esContainer = get_container_id('zammad-elasticsearch')
        
    # copy elasticsearch.yml from Elasticsearch docker into filesystem
    command_line = f'docker cp {esContainer}:/usr/share/elasticsearch/config/elasticsearch.yml .'
    run(command_line)

    file_path1 = Path(__file__).parent.absolute().joinpath("conf/elastic.yml")
    file_path2 = Path(__file__).parent.absolute().joinpath("elasticsearch.yml")

    # backup original elasticsearch.yml to elasticsearch.yml.old
    command_line = f'docker cp {file_path2} {esContainer}:/usr/share/elasticsearch/config/elasticsearch.yml.old'
    run(command_line)

    # read both yaml files as Dictionaries
    elastic_conf = yaml_loader(file_path1)
    elasticsearch_yml_orig = yaml_loader(file_path2)

    # Merge the dictionaries
    elasticsearch_yml_orig.update(elastic_conf)

    # Write the merged dictionary to a new file
    yaml_dumper(file_path2, elasticsearch_yml_orig)

    # copying new configuration into docker container and restart container
    command_line = f'docker cp elasticsearch.yml {esContainer}:/usr/share/elasticsearch/config/elasticsearch.yml'
    run(command_line)
    print(f'\nConfiguration updated, restarting elasticsearch')
    Path(file_path2).unlink(missing_ok=True)
    command_line = f'docker restart {esContainer}'
    run(command_line)
    print(f'restarted')
    return 0

def kibana_config(env):
    print(f"\nConfiguring kibana")
    
    kibContainer =get_container_id('zammad-kibana')
        
    # copy kibana.yml from kibana docker into filesystem
    command_line = f'docker cp {kibContainer}:/usr/share/kibana/config/kibana.yml .'
    run(command_line)

    file_path1 = Path(__file__).parent.absolute().joinpath("conf/kibana.yml")
    file_path2 = Path(__file__).parent.absolute().joinpath("kibana.yml")

    # backup original kibana.yml to kibana.yml.old
    command_line = f'docker cp {file_path2} {kibContainer}:/usr/share/kibana/config/kibana.yml.old'
    run(command_line)

    # read both yaml files as Dictionaries
    kibana_conf = yaml_loader(file_path1)
    kibana_yml_orig = yaml_loader(file_path2)

    # Merge the dictionaries
    kibana_yml_orig.update(kibana_conf)

    # Write the merged dictionary to a new file
    yaml_dumper(file_path2, kibana_yml_orig)

    # copying new configuration into docker container and restart container
    command_line = f'docker cp kibana.yml {kibContainer}:/usr/share/kibana/config/kibana.yml'
    run(command_line)
    print(f'\nConfiguration updated, restarting kibana')
    Path(file_path2).unlink(missing_ok=True)
    command_line = f'docker restart {kibContainer}'
    run(command_line)
    print(f'restarted')
    return 0

def main() -> int:
    import time

    parser = argparse.ArgumentParser(
        prog='zambana',
        description='Install Zammad with Kibana as docker-stack',
        epilog='May the force be with you'
    )

    parser.add_argument('-i', '--install', action='store_true',
                        help='installation without config')
    parser.add_argument('-u', '--uninstall',
                        action='store_true', help='uninstall docker-stack')
    parser.add_argument('-c', '--config', action='store_true',
                        help='only runs configurations')

    args = parser.parse_args()

    if args.uninstall:
        run('docker-compose down -v')
    else:
        if startup_check():
            run(f'{sys.executable} -m pip install -r {str(Path(__file__).parent.absolute().joinpath("requirements.txt"))}')
            from dotenv import dotenv_values
            env = dotenv_values(str(Path(__file__).parent.absolute())+"/.env")

            if not args.config:
                docker_install(env["PROJECT_NAME"])
            if not args.config and not args.install:
                for i in range(21):
                    sys.stdout.write('\r')
                    # the exact output you're looking for:
                    sys.stdout.write("Waiting: [%-20s] %d%%" % ('='*i, 5*i))
                    sys.stdout.flush()
                    time.sleep(1.5)
            if not args.install:
                zammad_config(env)
                elastic_config(env)
                kibana_config(env)
            print(
                f"\nDone.")
        else:
            return 1
    return 0


if __name__ == '__main__':
    import sys
    from pathlib import Path
    import argparse
    sys.exit(main())

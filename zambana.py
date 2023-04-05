
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
    args = shlex.split(cmd)
    #subprocess.check_call(args)
    with Popen(args, stdout=PIPE, stderr=None, shell=False) as process:
    #process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=None, shell=True)
        output, error = process.communicate()
    return output, error


def get_ip(ip_addr_proto="ipv4", ignore_local_ips=True):
    # By default, this method only returns non-local IPv4 addresses
    # To return IPv6 only, call get_ip('ipv6')
    # To return both IPv4 and IPv6, call get_ip('both')
    # To return local IPs, call get_ip(None, False)
    # Can combine options like so get_ip('both', False)
    from socket import getaddrinfo, gethostname
    import ipaddress
    af_inet = 2
    if ip_addr_proto == "ipv6":
        af_inet = 30
    elif ip_addr_proto == "both":
        af_inet = 0

    system_ip_list = getaddrinfo(gethostname(), None, af_inet, 1, 0)
    ip_list = []

    for ip in system_ip_list:
        ip = ip[4][0]

        try:
            ipaddress.ip_address(str(ip))
            ip_address_valid = True
        except ValueError:
            ip_address_valid = False
        else:
            if ipaddress.ip_address(ip).is_loopback and ignore_local_ips or ipaddress.ip_address(ip).is_link_local and ignore_local_ips:
                pass
            elif ip_address_valid:
                ip_list.append(ip)

    return ip_list


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

    
    '''
    TODO
        check = False
    if not Path(__file__).parent.absolute().joinpath("conf/kibana.yml").exists():
        print("Could not find kibana configuration - Aborting.")
        check = False
    '''
    return check


def docker_install(project_name):
    # installing docker stack
    print(f'\nInitalizing docker stack:')
    command_line = f"docker-compose -p {project_name} up -d"
    run(command_line)
    return


def zammad_config(env):
    print(f"\nConfiguring zammad")
    railsContainer = f'{env["PROJECT_NAME"]}_zammad-raisserver-1'
    output,error = run(f'docker container ls -f name={env["PROJECT_NAME"]}_zammad-rails -q')
    if error != None:
        print("Container railsserver not found: ABORT")
        run('docker compose down -v')
        exit
    else:
        railsContainer = output.decode("utf-8")[:-1]

    # read zammad.yml configuration file
    zammad_conf = yaml_loader(Path(__file__).parent.absolute().joinpath("conf/zammad.yml"))

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
        command_line = f'docker exec {railsContainer} rails r "{line}"'
        print(f"\nSetting {k}: {v}")
        output, error = run(command_line)
        if error != None:
            print(f'{k}couldn not be set - chek manually')
    return 0


def elastic_config(env):
    esContainer = f'{env["PROJECT_NAME"]}_zammad-es-1'
    output,error = run(f'docker container ls -f name={env["PROJECT_NAME"]}_zammad-es -q')
    if error != None:
        print("Container elasticsearch not found: ABORT")
        run('docker compose down -v')
        exit
    else:
        esContainer = output.decode("utf-8")[:-1]

    print(f"\nConfiguring elasticsearch")
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


def main() -> int:
    import time
    if startup_check():
        run(f'{sys.executable} -m pip install -r {str(Path(__file__).parent.absolute().joinpath("requirements.txt"))}')
        from dotenv import dotenv_values
        env = dotenv_values(str(Path(__file__).parent.absolute())+"/.env")

        docker_install(env["PROJECT_NAME"])
        time.sleep(10)
        zammad_config(env)
        elastic_config(env)
        print(
            f"\nDone. Open Zammad at http://{get_ip()[0]}:{env['ZAMMAD_PORT']}\nHave FUN!")

    else:
        return 1
    return 0


if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.exit(main())
    

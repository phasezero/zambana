#!/bin/bash
cd "$(dirname "$0")" || exit
function startup_check () {
    if ! command -v docker-compose &> /dev/null
        then
        echo "Could not find docker-compose. Check your docker installation."
        exit
    fi
    if [ ! -f ".env" ]
        then
        echo "Could not find .env - Aborting"
        exit
    fi
    if [ ! -f "scripts/backup.sh" ]
        then
        echo "Could not find .env - Aborting"
        exit
    else
    	chmod +x scripts/backup.sh
    fi

    # shellcheck source=.env
    source $PWD/.env

    if  docker compose ls | grep -q "$PROJECT_NAME"
    then
        echo -e "\nStack already exists! You will have to reconfigure PROJECT_NAME and service Ports in .env or it will crash!"
        echo "Good bye!"
        exit
    fi
}

function install_stack () {
    echo -e "\nStarting docker containers \n"
    docker-compose -p "$PROJECT_NAME" up -d
    wait $!
    # keep cool, it takes time
}

function config_zammad () {
    echo -e "\nConfiguring zammad"
    #sleep 5s
    # import zammd.conf for zammad configurations via rails
    while read -r line
    do
        varstr=$(echo "$line" | cut -d "'" -f 4 | sed 's/)$//')
        # needed to check if a value is configured in .env
        if [[ $varstr =~ ^\$.* ]]; then
            eval varstr_eval="$varstr"
            line=${line/$varstr/"$varstr_eval"}
        fi
        # execute rails in docker container
        docker exec "$PROJECT_NAME"-zammad-railsserver-1 rails r ""$line""
        wait $!
    done < <(grep -v '^#' "$1"/conf/zammad.conf)
}

function config_elastic () {
    echo -e "\nConfiguring elastichsearch"

}

startup_check
install_stack
config_zammad "$PWD"
config_elastic "$PWD"

echo -e "\nConfiguration done... finishing initialisation\n"
# wait till init docker is exited
while [ ! "$(docker ps -aq -f status=exited -f name="$PROJECT_NAME"-zammad-init-1)" ]
do
    sleep 5s
done
# remove elasticearch-setup docker
if [ "$(docker ps -aq -f status=exited -f name="$PROJECT_NAME"-zammad-es-setup-1)" ]; then
    echo -e Removing "$PROJECT_NAME"-zammad-es-setup-1
    docker container rm "$PROJECT_NAME"-zammad-es-setup-1 > /dev/null
    wait $!
fi
echo -e "\nInstallation finished. Zammad and elasticsearch connected.\nShould work now!"

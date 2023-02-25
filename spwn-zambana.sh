#!/bin/bash

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

# shellcheck source=.env
source .env

if  docker compose ls | grep -q "$PROJECT_NAME"
then
    echo -e "\nStack already exists! You will have to reconfigure PROJECT_NAME and service Ports in .env or it will crash!"
    echo "Good bye!"
    exit
else

# start docker-compose and wait 

echo -e "\nStarting docker containers \n"
cd "$(dirname $0)" || exit
chmod 775 scripts/bachup.sh
docker-compose -p "$PROJECT_NAME" up -d
wait $!
# keep cool, it takes time
sleep 10

echo -e "\nConfiguring elasticsearch connection"

# import zammd.conf for zammad configurations via rails
while read -r line
do
    varstr=$(echo "$line" | cut -d "'" -f 4 | sed 's/)$//')
    if [[ $varstr =~ ^\$.* ]]; then
        eval varstr_eval="$varstr"
        line=${line/$varstr/"$varstr_eval"}
    fi
    echo -e "\n$line"
    docker exec "$PROJECT_NAME"-zammad-init-1 rails r \""$line"\"
    wait $!
done < <(grep -v '^#' ./conf/zammad.conf)

echo -e "\nConnection configured. Finishing initialisation\n"

while [ "$(docker ps -aq -f status=exited -f name="$PROJECT_NAME"-zammad-init-1)" ]
do
    sleep 5s
done
if [ "$(docker ps -aq -f status=exited -f name="$PROJECT_NAME"-zammad-es-setup-1)" ]; then
    docker container rm "$PROJECT_NAME"-zammad-es-setup-1
    wait $!
fi
echo -e "\nInstallation finished. Connection with elasticsearch established.\nHave FUN!"
fi
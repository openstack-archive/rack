#!/bin/bash

set -x

META=$(curl -s http://169.254.169.254/openstack/latest/meta_data.json | jq '.meta')
RACK_PID=$(echo $META | jq -r '.pid')

# main
if [ "$RACK_PID" == "null" ]; then
  export COMPOSE_FILE=/root/docker-compose-api.yml
elif [ "$RACK_PID" != "null" ]; then
  export COMPOSE_FILE=/root/docker-compose-proxy.yml
fi

docker-compose up -d

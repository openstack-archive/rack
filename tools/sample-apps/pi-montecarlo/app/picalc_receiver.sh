#!/usr/bin/env sh

echo "OS_USERNAME="$OS_USERNAME
echo "OS_PASSWORD="$OS_PASSWORD
echo "OS_CONTAINER_NAME="$OS_CONTAINER_NAME
echo "OS_AUTH_URL="$OS_AUTH_URL
cd ~/rack/tools/sample-apps/pi-montecarlo/app
python picalc.py receiver $1 $2 $3 $4 $5
python put.py $OS_CONTAINER_NAME picalc_result
DATA=`curl http://169.254.169.254/openstack/latest/meta_data.json | jq .meta -r`
GID=`echo $DATA | jq .gid -r`
PID=`echo $DATA | jq .pid -r`
cd ~/rack/tools/;python ./rack_client.py --url http://$1:8088/v1/ process-delete --gid $GID --pid $PID

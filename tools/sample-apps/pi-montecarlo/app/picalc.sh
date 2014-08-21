#!/usr/bin/env sh

cd ~
RACK_CLIENT="python ./rack/tools/rack_client.py"
APP_PATH="~/rack/tools/sample-apps/pi-montecarlo/app"
GID=`curl http://169.254.169.254/openstack/latest/meta_data.json | jq '.meta.gid' -r`
DATA=`$RACK_CLIENT proxy-show --gid $GID`
PROXY_PID=`echo $DATA | jq '.proxy.pid' -r`
IP=`echo $DATA | jq .proxy.ipc_endpoint.host -r`
PORT=`echo $DATA | jq .proxy.ipc_endpoint.port -r`
OS_AUTH_URL=`echo $DATA | jq .proxy.fs_endpoint.host -r`
OS_CONTAINER_NAME=`echo $DATA | jq .proxy.fs_endpoint.name -r`
DATA=`$RACK_CLIENT securitygroup-list --gid $GID`
SGID=`echo $DATA | jq .securitygroups[0].securitygroup_id -r`

IMAGE=$1
TRIALS=$2
PROCESS_NUM=$3

rm -f .userdata
cat <<EOF>> .userdata
#!/usr/bin/env sh
echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ PI Calc Receiver Start! @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
export OS_USERNAME=$OS_USERNAME
export OS_TENANT_NAME=$OS_TENANT_NAME
export OS_PASSWORD=$OS_PASSWORD
export OS_AUTH_URL=$OS_AUTH_URL
export OS_CONTAINER_NAME=$OS_CONTAINER_NAME
cd $APP_PATH;./picalc_receiver.sh $IP $PORT $PROXY_PID $PROCESS_NUM $TRIALS $3
EOF

DATA=`$RACK_CLIENT process-create --gid $GID --name parent_p --nova_flavor_id 2 --glance_image_id $IMAGE --securitygroup_ids $SGID --userdata .userdata`
PARENTPID=`echo $DATA | jq .process.pid -r`
echo $PARENTPID
CHILD_TRIALS=`expr $TRIALS / $PROCESS_NUM`
sleep 15

rm -f .userdata
cat <<EOF>> .userdata
#!/usr/bin/env sh
echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ PI Calc Sender Start! @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
cd $APP_PATH;./picalc_sender.sh $IP $PORT $PROXY_PID $CHILD_TRIALS
EOF

for i in `seq 1 $PROCESS_NUM`
    $RACK_CLIENT process-create --gid $GID --name child_p_$i --nova_flavor_id 2 --glance_image_id $IMAGE --securitygroup_ids $SGID --ppid $PARENTPID --userdata .userdata
do
rm -f .userdata


#!/bin/bash

RACK_CONF="/etc/rack/rack.conf"
REDIS_CONF="/etc/redis.conf"
WS_PORT="8888"
metalist=$(curl -s http://169.254.169.254/openstack/latest/meta_data.json | jq '.meta')

if [ -e /etc/rack/rack.conf ]; then
  rm -f /etc/rack/rack.conf
fi
echo "[DEFAULT]" >> $RACK_CONF
echo "debug = True" >> $RACK_CONF
echo "verbose = True" >> $RACK_CONF
echo "rpc_backend = rack.openstack.common.rpc.impl_kombu" >> $RACK_CONF
echo "lock_path = /var/lib/rack/lock" >> $RACK_CONF
echo "state_path = /var/lib/rack" >> $RACK_CONF
echo "api_paste_config = /etc/rack/api-paste.ini" >> $RACK_CONF
echo "auth_strategy = noauth" >> $RACK_CONF
echo "log_dir=/var/log/rack" >> $RACK_CONF
echo "use_syslog=False" >> $RACK_CONF

sql_connection=`echo $metalist | jq '.sql_connection' -r`
echo "sql_connection="$sql_connection >> $RACK_CONF

rabbit_userid=`echo $metalist | jq '.rabbit_userid' -r`
echo "rabbit_userid="$rabbit_userid >> $RACK_CONF

rabbit_password=`echo $metalist | jq '.rabbit_password' -r`
echo "rabbit_password="$rabbit_password >> $RACK_CONF

rabbit_host=`echo $metalist | jq '.rabbit_host' -r`
echo "rabbit_host="$rabbit_host >> $RACK_CONF

roles=`echo $metalist | jq '.roles' -r`
echo "Roles:"$roles

mysql=`echo $roles | grep mysql | wc -l`
rabbitmq=`echo $roles | grep rabbitmq | wc -l`
api=`echo $roles | grep api | wc -l`
scheduler=`echo $roles | grep scheduler | wc -l`
resourceoperator=`echo $roles | grep resourceoperator | wc -l`
ipc=`echo $roles | grep ipc | wc -l`
shm=`echo $roles | grep shm | wc -l`

if [ 1 -eq $mysql ]; then
  echo "start mysql"
  service mysqld start
fi
if [ 1 -eq $rabbitmq ]; then
  echo "start RabbitMQ"
  service rabbitmq-server start
fi
if [ 1 -eq $api ]; then
  echo "start RACK-API"
  rack-api --config-file $RACK_CONF &
fi
if [ 1 -eq $scheduler ]; then
  echo "start RACK-Scheduler"
  rack-scheduler --config-file $RACK_CONF &
fi
if [ 1 -eq $resourceoperator ]; then
  os_username=`echo $metalist | jq '.os_username' -r`
  os_password=`echo $metalist | jq '.os_password' -r`
  os_tenant_name=`echo $metalist | jq '.os_tenant_name' -r`
  os_auth_url=`echo $metalist | jq '.os_auth_url' -r`

  echo "os_username="$os_username >> $RACK_CONF
  echo "os_password="$os_password >> $RACK_CONF
  echo "os_tenant_name="$os_tenant_name >> $RACK_CONF
  echo "os_auth_url="$os_auth_url >> $RACK_CONF

  echo "start RACK-ResourceOperator"
  rack-resourceoperator --config-file $RACK_CONF &
fi
if [ 1 -eq $ipc ]; then
  echo "start IPC(Websocket)"
  websocket_server $WS_PORT &
fi
if [ 1 -eq $shm ]; then
  echo "start SharedMemory(Redis)"
  redis-server $REDIS_CONF &
fi

proxy=`echo $roles | grep proxy | wc -l`
if [ 1 -eq $proxy ]; then
  gid=`echo $metalist | jq '.gid' -r`
  host=`/sbin/ifconfig | grep 'inet addr' | grep -v 127.0.0.1 | awk '{print $2;}' | cut -d: -f2`
  shm_port=`cat $REDIS_CONF | grep -v "#" | grep port | awk '{print $2;}'`
  echo "update proxy status and endpoints"
  sleep 10s
  export OS_USERNAME="demo_user"
  export OS_TENANT_NAME="demo_tenant"
  rack_client proxy-update --gid $gid --shm_endpoint {\"host\":\"$host\"\,\"port\":\"$shm_port\"} --ipc_endpoint {\"host\":\"$host\"\,\"port\":\"$WS_PORT\"} --app_status "ACTIVE"
fi


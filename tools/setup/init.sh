#!/bin/bash

set -x

RACK_CONF="/etc/rack/rack.conf"
REDIS_CONF="/etc/redis.conf"
META=$(curl -s http://169.254.169.254/openstack/latest/meta_data.json | jq '.meta')
RACK_GID=$(echo $META | jq -r '.gid')
RACK_PID=$(echo $META | jq -r '.pid')
OS_USERNAME=$(echo $META | jq -r '.os_username')
OS_PASSWORD=$(echo $META | jq -r '.os_password')
OS_TENANT_NAME=$(echo $META | jq -r '.os_tenant_name')
OS_AUTH_URL=$(echo $META | jq -r '.os_auth_url')
OS_REGION_NAME=$(echo $META | jq -r '.os_region_name')
if [ "$OS_USERNAME" == "null" ] || [ "$OS_PASSWORD" == "null" ] ||\
   [ "$OS_TENANT_NAME" == "null" ] || [ "$OS_AUTH_URL" == "null" ]; then
  echo "Error: OpenStack credentials are required."
  exit 1
fi
cat << EOF >> $RACK_CONF
os_username = $OS_USERNAME
os_password = $OS_PASSWORD
os_tenant_name = $OS_TENANT_NAME
os_auth_url = $OS_AUTH_URL
os_region_name = $OS_REGION_NAME
EOF


api() {
  service mysqld start || { echo "Error: mysqld could not start."; exit 1; }
  rack-api --config-file $RACK_CONF &
}

proxy() {
  rackapi_ip=$(echo $META | jq -r '.rackapi_ip')
  sed -i '/^sql_connection/d' $RACK_CONF
  echo "sql_connection = mysql://root:password@${rackapi_ip}/rack?charset=utf8" >> $RACK_CONF
  rack-api --config-file $RACK_CONF &

  websocket_server -d --bind-ipaddress 0.0.0.0 --bind-port 8888 --logfile /var/log/rack/ipc.log &
  service redis start || { echo "Error: redis could not start."; exit 1; }
  service rabbitmq-server start || { echo "Error: rabbitmq-server could not start."; exit 1; }
  service memcached start || { echo "Error: memcached could not start."; exit 1; }
  service xinetd start || { echo "Error: xinetd could not start."; exit 1; }
  swift-init main start && swift-init rest start || { echo "Error: Swift services could not start."; exit 1; }
}

# main
if [ "$RACK_PID" == "null" ]; then
  api
elif [ "$RACK_PID" != "null" ]; then
  proxy
fi

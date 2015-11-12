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

function exit_abort() {
  set +x
  echo "****************************************"
  echo "Error occurred."
  echo "Reason: $1"
  echo "****************************************"
  exit 1
}

api() {
  db="mysql://root:password@mysql/rack?charset=utf8"
  cd /app/rack/db/sqlalchemy/migrate_repo
  python manage.py version_control $db ||\
    exit_abort "Failed to create the migration table."
  python manage.py upgrade $db ||\
    exit_abort "Failed to create the database tables."
  rack-api --config-file $RACK_CONF
}

proxy() {
  rackapi_ip=$(python /app/tools/setup/get_rackapi_addr.py $OS_USERNAME $OS_PASSWORD $OS_TENANT_NAME $OS_AUTH_URL)
  pid=$(echo $META | jq -r '.pid')
  sed -i '/^sql_connection/d' $RACK_CONF
  echo "sql_connection = mysql://root:password@${rackapi_ip}/rack?charset=utf8" >> $RACK_CONF
  curl ${rackapi_ip}:8088/v1/groups/${gid}/processes/${pid} -X PUT \
  -H "Content-Type: application/json" \
  -d "{\"process\": {\"app_status\": \"ACTIVE\"}}"
  rack-api --config-file $RACK_CONF
}

# main
if [ "$RACK_PID" == "null" ]; then
  api
elif [ "$RACK_PID" != "null" ]; then
  proxy
fi

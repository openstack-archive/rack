#!/bin/sh

set -x

META_URL=http://169.254.169.254/openstack/latest/meta_data.json
META=$(curl -s $META_URL)
export RACK_GID=$(echo $META | jq -r ".meta.gid")
export RACK_PID=$(echo $META | jq -r ".meta.pid")
export RACK_PPID=$(echo $META | jq -r ".meta.ppid")
export RACK_PROXY_IP=$(echo $META | jq -r ".meta.proxy_ip")
export RACK_ENDPOINT=http://$RACK_PROXY_IP:8088/v1/
export OS_USERNAME=demo_user
export OS_TENANT_NAME=demo_user
PROXY_INFO=$(rack-client --url $RACK_ENDPOINT proxy-show --gid $RACK_GID | jq -r ".proxy")
ipc_host=$(echo $PROXY_INFO | jq -r ".ipc_endpoint.host")
ipc_port=$(echo $PROXY_INFO | jq -r ".ipc_endpoint.port")
export IPC_ENDPOINT=ws://$ipc_host:$ipc_port
export OS_USERNAME=$(echo $PROXY_INFO | jq -r ".fs_endpoint.os_username")
export OS_PASSWORD=$(echo $PROXY_INFO | jq -r ".fs_endpoint.os_password")
export OS_TENANT_NAME=$(echo $PROXY_INFO | jq -r ".fs_endpoint.os_tenant_name")
export OS_AUTH_URL=$(echo $PROXY_INFO | jq -r ".fs_endpoint.os_auth_url")

screen_it() {
  retval=$(screen -ls | grep -q main; echo $?)
  if [ "$retval" -ne 0 ]; then
    screen -d -m -S main -t shell -s /bin/bash
    sleep 1s
    screen -r main -X hardstatus alwayslastline '[%02c] %`%-w%{=b bw}%n %t%{-}%+w'
    screen -r main -X altscreen on
  fi
  NL=`echo -ne '\015'`
  screen -r main -X screen -t $1
  screen -r main -p $1 -X stuff "$2$NL"
}

parent() {
  service postgresql start
  service td-agent start
  export RACK_USERNAME=demo_user
  export RACK_TENANT_NAME=demo_user
  export MY_IPADDR=$(ifconfig eth0 | grep "inet addr" | awk '{print $2}' | awk -F":" '{print $2}')
  screen_it receptor "cd /opt/app/parent; python receptor.py"
  screen_it viewer "cd /opt/app/parent; python viewer.py"
  screen_it watcher "cd /opt/app/parent; python watcher.py --receptor_url http://localhost/fork --logdir /var/log/td-agent/twitter --prefix tweet --container $RACK_GID --db_connection postgresql://postgres@$MY_IPADDR/pndb"
}

child() {
  export file_name=$(echo $META | jq -r ".meta.file_name")
  export db_connection=$(echo $META | jq -r ".meta.db_connection")
  screen_it analyzer "cd /opt/app/child; python analyzer.py"
}

# main
if [ $RACK_PPID == $RACK_PID ]; then
  parent
else
  child
fi

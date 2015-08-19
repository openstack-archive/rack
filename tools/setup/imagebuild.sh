#!/bin/sh

set -x

########################################
# Declare Variables and Functions
########################################
### variables ###
ROOT_DIR=$(cd $(dirname "$0") && cd ../../ && pwd)

### functions ###
function exit_abort() {
  set +x
  echo "****************************************"
  echo "Error occurred."
  echo "Reason: $1"
  echo "****************************************"
  exit 1
}


########################################
# Start Message
########################################
echo "Start RACK image building..."


########################################
# Update System
########################################
echo "Update system..."
yum update -y || exit_abort "Failed to execute 'yum update'"


########################################
# Check and Install Addtional Repositories
########################################
echo "Ensure that EPEL repository is installed..."
if ! yum repolist enabled epel | grep -q epel; then
  yum install -y https://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm || \
    exit_abort "Failed to install EPEL repository"
fi


########################################
# Check and Install Packages
########################################
echo "Ensure that the required packages are installed..."
yum -y install \
  libffi-devel libgcc-devel gcc python-devel python-lxml libxslt-devel \
  libxml2-devel openssl-devel MySQL-python mysql-server python-pip redis \
  rabbitmq-server || \
    exit_abort "Failed to install the required rpm packages"

service iptables stop

########################################
# Setup MySQL
########################################
echo "Setup MySQL..."
service mysqld restart || exit_abort "Failed to start mysqld"
mysqladmin -u root password password
mysql -uroot -ppassword -h127.0.0.1 -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by 'password';"


########################################
# Setup Redis
########################################
echo "Setup Redis..."
sed -i -e "s/bind 127.0.0.1/bind 0.0.0.0/g" /etc/redis.conf
service redis restart || exit_abort "Failed to start redis"


########################################
# Setup RabbitMQ
########################################
echo "Setup RabbitMQ..."
/usr/lib/rabbitmq/bin/rabbitmq-plugins enable rabbitmq_management
service rabbitmq-server restart || exit_abort "Failed to start rabbitmq-server"


########################################
# Deploy RACK
########################################
echo "Deploy RACK..."

### install RACK ###
cd $ROOT_DIR
pip install -U setuptools
pip install -r requirements.txt || exit_abort "Failed to install the RACK requirements"
retval=$(which rack-api > /dev/null 2>&1; echo $?)
if [ "$retval" -ne 0 ]; then
  python setup.py install || exit_abort "Failed to install RACK"
fi

### create DB tables ###
mysql -uroot -ppassword -e "DROP DATABASE IF EXISTS rack"
mysql -uroot -ppassword -e "CREATE DATABASE rack CHARACTER SET utf8;"
cd $ROOT_DIR/rack/db/sqlalchemy/migrate_repo
python manage.py version_control mysql://root:password@localhost/rack ||\
  exit_abort "Failed to create the migration table"
python manage.py upgrade mysql://root:password@localhost/rack ||\
  exit_abort "Failed to create the database tables"

### install jq ###
wget -q -O /usr/bin/jq http://stedolan.github.io/jq/download/linux64/jq ||\
  exit_abort "Failed to download jq"
chmod +x /usr/bin/jq

### configure RACK ###
rm -fr /etc/rack /var/log/rack /var/lib/rack/lock
mkdir -p /etc/rack /var/log/rack /var/lib/rack/lock
cp -f $ROOT_DIR/etc/api-paste.ini /etc/rack/api-paste.ini
cat << EOF > /etc/rack/rack.conf
[DEFAULT]
debug = True
verbose = True
lock_path = /var/lib/rack/lock
state_path = /var/lib/rack
sql_connection = mysql://root:password@127.0.0.1/rack?charset=utf8
api_paste_config = /etc/rack/api-paste.ini
auth_strategy = noauth
log_dir = /var/log/rack
use_syslog = False
EOF

### deploy init script ###
rm -f /usr/bin/init.sh
cp -f $ROOT_DIR/tools/setup/init.sh /usr/bin/init.sh
chmod +x /usr/bin/init.sh
if ! grep -q init.sh /etc/rc.local; then
  echo "init.sh" >> /etc/rc.local
fi

### deploy websocket server application ###
rm -f /usr/bin/websocket_server
cp -f $ROOT_DIR/tools/setup/websocket_server.py /usr/bin/websocket_server
chmod +x /usr/bin/websocket_server


########################################
# Prepare for Save as Snapshot
########################################
chkconfig mysqld off
chkconfig redis off
chkconfig iptables off
chkconfig rabbitmq-server off

# set SELinux disabled
sed -i "s/\(^SELINUX=\).*/\1Disabled/" /etc/selinux/config

# reset nic information
rm -f /etc/udev/rules.d/70-persistent-net.rules


########################################
# Finish Message
########################################
set +x
echo "
****************************************
Finish RACK image building.
Shutdown and save snapshot of this instance via Horizon or glance command.
****************************************
"

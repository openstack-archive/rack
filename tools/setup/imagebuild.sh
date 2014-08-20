#!/bin/sh

set -x

########################################
# Declare Variables and Functions
########################################
### variables ###
ROOT_DIR=$(cd $(dirname "$0") && cd ../../ && pwd)

### functions ###
function exit_abort() {
  echo "Finished: ABORT"
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
yum update -y


########################################
# Check and Install Addtional Repositories
########################################
echo "Ensure that EPEL repository is resistered..."
if ! yum repolist enabled epel groonga | grep -q epel; then
yum install -y \
https://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm || echo "ERROR: EPEL repository could not be registered" exit_abort
fi


########################################
# Check and Install Packages
########################################
echo "Ensure that the required packages are installed..."
yum -y install libffi-devel libgcc-devel gcc python-devel python-lxml libxslt-devel libxml2-devel openssl-devel MySQL-python
for i in rabbitmq-server mysql-server python-setuptools redis; do
  yum install -y $i
  if [ $? -ne 0 ]; then
    echo "ERROR:$i could not be installed"
    exit_abort
  fi
done
sed -i -e "s/bind 127.0.0.1/bind 0.0.0.0/g" /etc/redis.conf
chkconfig rabbitmq-server off
chkconfig mysqld off
chkconfig iptables off
service mysqld start || exit_abort
service rabbitmq-server start || exit_abort
service iptables stop || exit_abort

easy_install pip
pip install gevent-websocket
if [ $? -ne 0 ]; then
  echo "ERROR:gevent-websocket could not be installed"
  exit_abort
fi

########################################
# Setup MySQL
########################################
mysqladmin -u root password password
mysql -uroot -ppassword -h127.0.0.1 -e "GRANT ALL PRIVILEGES ON *.* TO
'root'@'%' identified by 'password';"


########################################
# Deploy RACK
########################################
echo "Deploy RACK..."

### install RACK ###
cd $ROOT_DIR
pip install -r requirements.txt
python setup.py install

### create DB tables ###
mysql -uroot -ppassword -e "CREATE DATABASE rack CHARACTER SET utf8"
cd $ROOT_DIR/rack/db/sqlalchemy/migrate_repo
python manage.py version_control mysql://root:password@localhost/rack
python manage.py upgrade mysql://root:password@localhost/rack

### install jq ###
wget -q -O /usr/bin/jq http://stedolan.github.io/jq/download/linux64/jq
if [ $? -ne 0 ];then
  echo "ERROR:jq command could not download."
  exit_abort
fi
chmod +x /usr/bin/jq

### deploy init script ###
cp -f $ROOT_DIR/tools/setup/rack-init.sh /usr/bin/init.sh
echo "init.sh" >> /etc/rc.local
cp -f $ROOT_DIR/tools/rack_client.py /usr/bin/rack_client
chmod +x /usr/bin/rack_client
mkdir /var/log/rack

pip install -U setuptools

########################################
# Prepare for Save as Snapshot
########################################
rm -f /etc/udev/rules.d/70-persistent-net.rules


########################################
# Finish Message
########################################
echo "
****************************************
Finish RACK image building.
Shutdown and save snapshot of this instance via Horizon or glance command.
****************************************
"

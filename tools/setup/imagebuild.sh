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
if ! yum repolist enabled openstack-icehouse | grep -q openstack-icehouse; then
  yum install -y https://rdo.fedorapeople.org/openstack-icehouse/rdo-release-icehouse.rpm || \
    exit_abort "Failed to install RDO repository"
fi


########################################
# Check and Install Packages
########################################
echo "Ensure that the required packages are installed..."
yum -y install \
  libffi-devel libgcc-devel gcc python-devel python-lxml libxslt-devel \
  libxml2-devel openssl-devel MySQL-python mysql-server python-pip redis \
  openstack-swift openstack-swift-proxy openstack-swift-account openstack-swift-container \
  openstack-swift-object memcached rsync xinetd openstack-utils xfsprogs || \
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
# Deploy RACK
########################################
echo "Deploy RACK..."

### install RACK ###
cd $ROOT_DIR
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
# Install python-rackclient
########################################
echo "Install python-rackclient..."
retval=$(which rack > /dev/null 2>&1; echo $?)
if [ "$retval" -ne 0 ]; then
  rm -fr ~/python-rackclient
  git clone https://github.com/stackforge/python-rackclient.git ~/python-rackclient ||\
    exit_abort "Failed to clone python-rackclient repository"
  cd ~/python-rackclient
  pip install -r requirements.txt || exit_abort "Failed to install the rackclient requirements"
  python setup.py install || exit_abort "Failed to install rackclient"
fi



########################################
# Setup Swift
########################################
# configure rsync daemon
cat << EOF > /etc/rsyncd.conf
uid = swift
gid = swift
log file = /var/log/rsyncd.log
pid file = /var/run/rsyncd.pid
address =0.0.0.0

[account]
max connections = 2
path = /srv/node/
read only = false
lock file = /var/lock/account.lock

[container]
max connections = 2
path = /srv/node/
read only = false
lock file = /var/lock/container.lock

[object]
max connections = 2
path = /srv/node/
read only = false
lock file = /var/lock/object.lock
EOF

sed -i "s/\(^ *disable =\) yes/\1 no/" /etc/xinetd.d/rsync

# mount a loopback device for Swift storage node
umount /srv/node/part1 > /dev/null 2>&1
rm -fr /srv/node/part1
mkdir -p /srv/node/part1
rm -fr /srv/swift-disk
dd if=/dev/zero of=/srv/swift-disk bs=1GB count=10 || exit_abort "(Swift setup) Failed to create a dummy file"
mkfs.xfs /srv/swift-disk || exit_abort "(Swift setup) Failed to make a XFS file system"
if ! grep -q /srv/node/part1 /etc/fstab; then
  echo "/srv/swift-disk /srv/node/part1 xfs loop,noatime,nodiratime,nobarrier,logbufs=8 0 0" >> /etc/fstab
fi
mount /srv/node/part1 || exit_abort "(Swift setup) Failed to mount a loopback device"
chown -R swift:swift /srv/node

# configure swift.conf
openstack-config --set /etc/swift/swift.conf swift-hash swift_hash_path_suffix realapplicationcentrickernel

# configure account-server.conf
openstack-config --set /etc/swift/account-server.conf DEFAULT bind_ip 127.0.0.1
openstack-config --set /etc/swift/account-server.conf DEFAULT user swift
openstack-config --set /etc/swift/account-server.conf DEFAULT devices /srv/node

# configure container-server.conf
openstack-config --set /etc/swift/container-server.conf DEFAULT bind_ip 127.0.0.1
openstack-config --set /etc/swift/container-server.conf DEFAULT user swift
openstack-config --set /etc/swift/container-server.conf DEFAULT devices /srv/node

# configure object-server.conf
openstack-config --set /etc/swift/object-server.conf DEFAULT bind_ip 127.0.0.1
openstack-config --set /etc/swift/object-server.conf DEFAULT user swift
openstack-config --set /etc/swift/object-server.conf DEFAULT devices /srv/node

# configure proxy-server.conf
openstack-config --set /etc/swift/proxy-server.conf DEFAULT bind_ip 0.0.0.0
openstack-config --set /etc/swift/proxy-server.conf DEFAULT workers 1
openstack-config --set /etc/swift/proxy-server.conf DEFAULT user swift
openstack-config --set /etc/swift/proxy-server.conf pipeline:main pipeline "healthcheck cache tempauth proxy-server"
openstack-config --set /etc/swift/proxy-server.conf filter:tempauth use egg:swift#tempauth
openstack-config --set /etc/swift/proxy-server.conf filter:tempauth user_rack_admin "admin .admin"

# resister ring files
cd /etc/swift
swift-ring-builder account.builder create 18 1 1
swift-ring-builder container.builder create 18 1 1
swift-ring-builder object.builder create 18 1 1
swift-ring-builder account.builder add z0-127.0.0.1:6002/part1 100
swift-ring-builder container.builder add z0-127.0.0.1:6001/part1 100
swift-ring-builder object.builder add z0-127.0.0.1:6000/part1 100
swift-ring-builder account.builder rebalance
swift-ring-builder container.builder rebalance
swift-ring-builder object.builder rebalance
chown -R swift:swift /etc/swift

# check if the services work
service memcached restart || exit_abort "Failed to start memcached"
service xinetd restart || exit_abort "Failed to start xinetd"
swift-init main start || exit_abort "Failed to start the main Swift services"
swift-init rest start || exit_abort "Failed to start the rest of the Swift services"


########################################
# Prepare for Save as Snapshot
########################################
chkconfig mysqld off
chkconfig redis off
chkconfig iptables off

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

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
# Check and Install Packages
########################################
echo "Ensure that the required packages are installed..."
yum -y install docker

# Install docker-compose
curl -L https://github.com/docker/compose/releases/download/1.5.0/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

### install jq ###
curl -L http://stedolan.github.io/jq/download/linux64/jq > /usr/local/bin/jq
chmod +x /usr/local/bin/jq

########################################
# Deploy RACK
########################################
echo "Deploy RACK..."

### deploy init script ###
rm -f /usr/local/bin/init.sh
cp -f $ROOT_DIR/tools/setup/vm-init.sh /usr/local/bin/init.sh
chmod +x /usr/local/bin/init.sh

cp -f $ROOT_DIR/tools/setup/rack.service /etc/systemd/system

rm -f /root/docker-compose*.yml
cp -f $ROOT_DIR/tools/setup/docker-compose*.yml /root

# service
systemctl enable docker.service
systemctl enable rack.service

# clean cache
yum clean all

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

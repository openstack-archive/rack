#!/bin/sh

set -x

########################################
# Declare Variables and Functions
########################################
### variables ###
CURRENT_DIR=$(cd $(dirname "$0") && pwd)
APP_DIR=/opt/app

### functions ###
function exit_abort() {
  set +x
  echo "****************************************"
  echo "Error occurred. Execution aborted."
  echo $1
  echo "****************************************"
  exit 1
}


########################################
# Start Message
########################################
echo "Start image building..."


########################################
# Update System
########################################
echo "Update system..."
yum update -y || exit_abort "Error: Updating system"


########################################
# Check and Install Addtional Repositories
########################################
echo "Ensure that EPEL repository is installed..."
if ! yum repolist enabled epel | grep -q epel; then
  yum install -y https://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm || \
    exit_abort "Error: Installing EPEL repository"
fi


########################################
# Check and Install Packages
########################################
echo "Ensure that the required packages are installed..."
yum -y install python-pip || \
    exit_abort "Error: Installing the required packages"


########################################
# Deploy application
########################################
echo "Deploy application..."

### deploy application ###
rm -fr $APP_DIR
mkdir -p $APP_DIR
cp -fr $CURRENT_DIR/app/* $APP_DIR

### install python libraries ###
pip install -r $CURRENT_DIR/requirements.txt || exit_abort "Error: Installing the required python packages of app"

### deploy init script ###
retval=$(which init.sh > /dev/null 2>&1; echo $?)
if [ "$retval" -ne 0 ]; then
  cp -f $CURRENT_DIR/init.sh /usr/bin/init.sh
  chmod +x /usr/bin/init.sh
  echo "init.sh" >> /etc/rc.local
fi

### install rack client ###
retval=$(which rack > /dev/null 2>&1; echo $?)
if [ "$retval" -ne 0 ]; then
  git clone https://github.com/stackforge/python-rackclient.git ~/python-rackclient ||\
    exit_abort "Error: Cloning python-rackclient repository"
  cd ~/python-rackclient
  pip install -r requirements.txt || exit_abort "Error: Installing the required python packages of rackclient"
  python setup.py install || exit_abort "Error: Installing rackclient"
fi


########################################
# Prepare for Save as Snapshot
########################################
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
Finish image building.
Shutdown and save snapshot of this instance via Horizon or glance command.
****************************************
"

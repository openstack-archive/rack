#!/bin/sh

set -x

########################################
# Fill in the blanks
API_KEY=
API_SECRET=
ACCESS_TOKEN=
ACCESS_TOKEN_SECRET=
KEYWORDS=
########################################


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
yum update -y


########################################
# Check and Install Addtional Repositories
########################################
echo "Ensure that additional repositories are resistered..."
if ! yum repolist enabled epel | grep epel > /dev/null 2>&1; then
  yum install -y https://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm || exit_abort
fi


########################################
# Check and Install Packages
########################################
echo "Ensure that the required packages are installed..."
yum install -y \
    gcc gcc-c++ python-devel openssl-devel postgresql-server postgresql-devel python-setuptools \
    python-keystoneclient python-swiftclient screen || exit_abort
chkconfig postgresql off
chkconfig iptables off
easy_install pip  || exit_abort


########################################
# Setup Fluentd
########################################
echo "Setup Fluentd..."
curl -L http://toolbelt.treasuredata.com/sh/install-redhat.sh | sh  || exit_abort
/usr/lib64/fluent/ruby/bin/fluent-gem install fluent-plugin-twitter  || exit_abort

### configure Fluentd ###
rm -f /etc/td-agent/td-agent.conf
cat << EOF > /etc/td-agent/td-agent.conf
<source>
  type twitter
  consumer_key        $API_KEY
  consumer_secret     $API_SECRET
  oauth_token         $ACCESS_TOKEN
  oauth_token_secret  $ACCESS_TOKEN_SECRET
  tag                 input.twitter
  timeline            sampling
  keyword             $KEYWORDS
  lang                en
  output_format       simple
</source>

<match input.twitter>
  type              file
  path              /var/log/td-agent/twitter/tweet.log
  time_slice_format %Y%m%d-%H%M
  time_slice_wait   1m
  compress          gzip
</match>
EOF


########################################
# Setup PostgreSQL
########################################
echo "Setup PostgreSQL..."
service postgresql stop
rm -fr /var/lib/pgsql/data
service postgresql initdb || exit_abort
rm -f /var/lib/pgsql/data/pg_hba.conf
cat << EOF > /var/lib/pgsql/data/pg_hba.conf
local   all         all                               trust
host    all         all         0.0.0.0/0             trust
host    all         all         ::1/128               trust
EOF
echo "listen_addresses = '*'" >> /var/lib/pgsql/data/postgresql.conf
service postgresql start || exit_abort
sudo -u postgres -i env createdb pndb || exit_abort


########################################
# Setup TreeTagger
########################################
echo "Setup TreeTagger..."
### install TreeTagger ###
mkdir -p /opt/treetagger
cd /opt/treetagger
wget http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english-par-linux-3.2-utf8.bin.gz \
    http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh \
    http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz \
    http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.tar.gz || exit_abort
sh install-tagger.sh || exit_abort
ln -s /opt/treetagger/cmd/tree-tagger-english /usr/bin/tree-tagger-english

### install TreeTagger python client ###
easy_install -U distribute
pip install nltk
git clone https://github.com/miotto/treetagger-python.git || exit_abort
cd treetagger-python
python setup.py install || exit_abort


########################################
# Deploy applications
########################################
echo "Deploy applications..."

### deploy applications directory ###
rm -fr $APP_DIR
mkdir -p $APP_DIR
cp -fr $CURRENT_DIR/app/* $APP_DIR

### install python libraries ###
pip install -r $CURRENT_DIR/requirements.txt  || exit_abort

### get pn dictionary ###
wget -O $APP_DIR/child/pn_en.dic http://www.lr.pi.titech.ac.jp/~takamura/pubs/pn_en.dic || exit_abort

### create DB tables ###
rm -f /tmp/pndb.sql
cp -f $CURRENT_DIR/pndb.sql /tmp
chown postgres:postgres /tmp/pndb.sql
sudo -u postgres -i env psql -d pndb -f /tmp/pndb.sql || exit_abort

### install jq ###
retval=$(which jq > /dev/null 2>&1; echo $?)
if [ "$retval" -ne 0 ]; then
  wget -q -O /usr/bin/jq http://stedolan.github.io/jq/download/linux64/jq || exit_abort
  chmod +x /usr/bin/jq
fi

### deploy init script ###
retval=$(which init.sh > /dev/null 2>&1; echo $?)
if [ "$retval" -ne 0 ]; then
  cp -f $CURRENT_DIR/init.sh /usr/bin/init.sh
  chmod +x /usr/bin/init.sh
  echo "init.sh" >> /etc/rc.local
fi

### deploy rack-client ###
retval=$(which rack-client > /dev/null 2>&1; echo $?)
if [ "$retval" -ne 0 ]; then
  cp -f $CURRENT_DIR/rack-client /usr/bin/rack-client
  chmod +x /usr/bin/rack-client
fi


########################################
# Prepare for Save as Snapshot
########################################
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

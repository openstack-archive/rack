#!/usr/bin/env sh

APP_PATH=~/rack/tools/sample-apps/pi-montecarlo
yum install git -y
easy_install pip
pip install -U setuptools
git clone https://github.com/stackforge/rack.git ~/rack
pip install -r $APP_PATH/requirement.txt

curl -o /usr/bin/jq http://stedolan.github.io/jq/download/linux64/jq
chmod +x /usr/bin/jq
chmod +x $APP_PATH/app/*.sh

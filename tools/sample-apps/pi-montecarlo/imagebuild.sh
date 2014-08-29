#!/usr/bin/env sh

easy_install pip
git clone https://github.com/stackforge/rack.git ~/rack
pip install -r ./requirements.txt

curl -o /usr/bin/jq http://stedolan.github.io/jq/download/linux64/jq
chmod +x /usr/bin/jq
chmod +x ./app/*.sh


#!/usr/bin/env sh

yum update -y
easy_install pip
pip install -r ./requirements.txt
curl -o /usr/bin/jq http://stedolan.github.io/jq/download/linux64/jq
chmod +x /usr/bin/jq

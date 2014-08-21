#!/usr/bin/env python
"""
Tweet Extractor via td-agent

source openrc
python tweet_extractor.py --logdir /path/to/{your logs dicectry} --prefix {log prefix} --container {swift container name}
"""

import sys
import time
import json
import argparse
import os
import re
import logging
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from swiftclient import client as swift_client  

logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s %(filename)s:%(lineno)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

class MyEventHandler(FileSystemEventHandler):   
    def __init__(self, args):
        self.args = args
        self.swift = get_swift_client(self.args)

    def on_created(self, event):
        logging.info("File " + event.src_path + " created")
        regex = re.compile(self.args.prefix + "\.log\..+\.log\.gz")
        path = event.src_path
        file_name = os.path.basename(path)
        if regex.match(file_name):
            f = open(path, "r")
            self.swift.put_object(self.args.container, file_name, f)
            logging.info("File " + event.src_path + " uploaded to Swift")
            f.close()
            boot_process(self.args.receptor_url, file_name, self.args.db_connection)


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receptor_url", help="reception process URL", required=True)
    parser.add_argument("--logdir", help="log file directory", required=True)
    parser.add_argument("--prefix", help="log file prefix", required=True)
    parser.add_argument("--container", help="swift container name", required=True)
    parser.add_argument("--db_connection", help="viewer db connection", required=True)
    parser.add_argument("--os-username", default=os.getenv("OS_USERNAME"))
    parser.add_argument("--os-password", default=os.getenv("OS_PASSWORD"))
    parser.add_argument("--os-tenant_name", default=os.getenv("OS_TENANT_NAME"))
    parser.add_argument("--os-auth_url", default=os.getenv("OS_AUTH_URL"))
    return parser.parse_args()


def boot_process(url, file_name, db_connection):
    headers = {"content-type": "application/x-www-form-urlencoded"}
    data = {
        "file_name": file_name,
        "db_connection": db_connection
    }
    res = requests.post(url, data=data, headers=headers)
    logging.info("Fork executed. HTTP code: %s" % res.status_code)
    logging.info(res.json())


def get_swift_client(args):
    credentials = {
        "user": args.os_username,
        "key": args.os_password,
        "tenant_name": args.os_tenant_name,
        "authurl": args.os_auth_url,
        "auth_version": "2"
    }
    return swift_client.Connection(**credentials)


if __name__ == "__main__":
    args = make_parser()
    event_handler = MyEventHandler(args)
    observer = Observer()
    observer.schedule(event_handler, args.logdir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

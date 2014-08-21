#!/usr/bin/python
"""
Tweet Analyzer powered by MeCab
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gzip
import json
import time
import logging
from swiftclient import client as swift_client
from datetime import datetime
from treetagger import TreeTagger
from db import models
import websocket_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s %(filename)s:%(lineno)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


TT = TreeTagger(encoding='latin-1',language='english')
NOUNS = ("NNS", "NP", "NPS")
VERBS = ("VM", "VBD", "VBG", "VBN", "VBP", "VBZ")
ADJECTIVES = ("JJ", "JJR", "JJS")
ADVERBS = ("RB", "RBR", "RBS","WRB")
CATEGORIES = NOUNS + VERBS + ADJECTIVES + ADVERBS


def make_pnlist(path):
    keys = ["word", "category", "score"]
    pnlist = []
    for f in open(path, "r"):
        pnlist.append(dict(zip(keys, f.split(":"))))
    return pnlist


def analyzer(msg, pnlist):
    morpheme_list = TT.tag(msg.encode("utf-8").lower())

    total = 0
    count = 0
    for morpheme in morpheme_list:
        if morpheme[1] in CATEGORIES:
            if morpheme[1] in NOUNS:
                category = "n"
            elif morpheme[1] in VERBS:
                category = "v"
            elif morpheme[1] in ADJECTIVES:
                category = "a"
            else:
                category = "r"

            for pn in pnlist:
                if pn["word"] == morpheme[0] and pn["category"] == category:
                    total += float(pn["score"])
                    count += 1
                    break

    if count > 0:
        return float(total / count)
    else:
        return 0


def get_file_from_swift(context):
    credentials = {
        "user": context["os_username"],
        "key": context["os_password"],
        "tenant_name": context["os_tenant_name"],
        "authurl": context["os_auth_url"],
        "auth_version": "2"
    }
    swift = swift_client.Connection(**credentials)
    target = swift.get_object(context["gid"], context["file_name"])
    f = open(os.path.dirname(__file__) + context["file_name"], "w")
    f.write(target[1])
    f.close()


def get_context():
    return {
        "username": os.getenv("RACK_USERNAME"),
        "tenant_name": os.getenv("RACK_TENANT_NAME"),
        "gid": os.getenv("RACK_GID"),
        "pid": os.getenv("RACK_PID"),
        "ppid": os.getenv("RACK_PPID"),
        "ws_endpoint": os.getenv("IPC_ENDPOINT"),
        "os_username": os.getenv("OS_USERNAME"),
        "os_password": os.getenv("OS_PASSWORD"),
        "os_tenant_name": os.getenv("OS_TENANT_NAME"),
        "os_auth_url": os.getenv("OS_AUTH_URL"),
        "file_name": os.getenv("file_name"),
        "db_connection": os.getenv("db_connection")
    }


def main():
    context = get_context()
    models.CONN = context["db_connection"]
    get_file_from_swift(context)

    scores = []
    created_at = []
    for f in gzip.open(context["file_name"], "r"):
        tweet = json.loads(f.split("\t")[2])
        created_at.append(tweet["created_at"])
        scores.append(analyzer(tweet["message"], make_pnlist("pn_en.dic")))

    d_fmt = "%a %b %d %H:%M:%S +0000 %Y"
    start_datetime = datetime.strptime(created_at[0], d_fmt)
    end_datetime = datetime.strptime(created_at[-1], d_fmt)
    avg_score = float(sum(scores) / len(scores))

    d = {
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "avg_score": avg_score
    }
    models.insert_score(d)
    websocket_client.send(
        ws_endpoint=context["ws_endpoint"],
        header=context["ppid"],
        message=context["pid"]
    )


if __name__ == "__main__":
    time1 = time.clock()
    main()
    time2 = time.clock()
    exec_time = int(time2 - time1)
    logging.info("Execution time: " + str(exec_time) + "seconds")
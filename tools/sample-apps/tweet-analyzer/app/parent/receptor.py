import argparse
import json
import logging
from flask import Flask
from flask.ext import restful
from flask_restful import reqparse
import os
import requests
import sys
sys.path.append("../" + os.path.dirname(__file__))
import websocket_client
import eventlet

eventlet.monkey_patch()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s %(filename)s:%(lineno)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

app = Flask(__name__)
api = restful.Api(app)

parser = reqparse.RequestParser()
parser.add_argument("file_name", type=str)
parser.add_argument("db_connection", type=str)

def get_context():
    return {
        "endpoint": os.getenv("RACK_ENDPOINT"),
        "gid": os.getenv("RACK_GID"),
        "pid": os.getenv("RACK_PID"),
        "ws_endpoint": os.getenv("IPC_ENDPOINT"),
        "username": os.getenv("RACK_USERNAME"),
        "tenant_name": os.getenv("RACK_TENANT_NAME")
    }


class Fork(restful.Resource):
    def post(self):
        args = parser.parse_args()
        if not args["file_name"]:
            return {"BadRequest": "file_name is required"}, 400
        if not args["db_connection"]:
            return {"BadRequest": "db_connection is required"}, 400

        context = get_context()
        try:
            start_analyze(context, args["file_name"], args["db_connection"])
        except Exception as e:
            logging.exception(e)
            return {"Internal Server Error": e.message}, 500
        return {"Accepted": "Request accepted"}, 202


api.add_resource(Fork, '/fork')


def start_analyze(context, file_name, db_connection):
    url = context["endpoint"] + "/groups/" + context["gid"] + "/processes"
    headers = {
        "content-type": "application/json",
        "accept": "application/json",
        "X-Auth-Token": ":".join([context["username"], context["tenant_name"]])
    }
    payload = {
        "ppid": context["pid"],
        "name": "child",
        "args": {
            "file_name": file_name,
            "db_connection":db_connection
        }
    }
    data = json.dumps(dict(process=payload))
    res = requests.post(url, data=data, headers=headers)
    if res.status_code != 202:
        raise Exception("Fork failed")


def main():
    context = get_context()
    w = websocket_client.Receiver(
        rack_endpoint=context["endpoint"],
        gid=context["gid"],
        ws_endpoint=context["ws_endpoint"],
        rack_username=context["username"],
        rack_tenant_name=context["tenant_name"]
    )
    eventlet.spawn_n(w.receive, context["pid"])
    app.run(host="0.0.0.0", port=80)

if __name__ == '__main__':
    main()

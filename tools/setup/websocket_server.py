#!/usr/bin/python

import argparse
import logging
import sys
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
import os

LOG = logging.getLogger(__name__)


def set_debugging(debug=False, logfile=None):
    if debug:
        format = "%(asctime)s %(levelname)s - %(message)s %(filename)s:%(lineno)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        if logfile and os.path.exists(os.path.dirname(logfile)):
            logging.basicConfig(level=logging.DEBUG, format=format, datefmt=datefmt, filename=logfile)
        else:
            logging.basicConfig(level=logging.DEBUG, format=format, datefmt=datefmt)


class RackApplication(WebSocketApplication):
    connections = {}

    def on_open(self):
        pid = self.ws.environ.get("HTTP_PID")
        path = self.ws.environ.get("PATH_INFO")
        if pid and path == '/receive':
            self.connections[pid] = self.ws
        LOG.debug("Connection for %s opened", pid)

    def on_message(self, message):
        if self.ws.environ:
            pid = self.ws.environ.get("HTTP_PID")
            path = self.ws.environ.get("PATH_INFO")
            if pid and path == '/send':
                conn = self.connections.get(pid)
                if conn:
                    LOG.debug("Send a message to the connection for %s", pid)
                    LOG.debug("Message: %s", message)
                    conn.send(message)

    def on_close(self, reason):
        LOG.debug("Connection closed")


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--debug',
        default=False,
        action='store_true',
        help="Print debugging output"
    )
    parser.add_argument(
        '--logfile',
        metavar='PATH',
        help="Path of log file to output to"
    )
    parser.add_argument(
        '--bind-ipaddress',
        metavar='<bind-ipaddress>',
        dest='ipaddr',
        default='127.0.0.1'
    )
    parser.add_argument(
        '--bind-port',
        metavar='<bind-port>',
        type=int,
        dest='port',
        default=8888
    )
    return parser

if __name__ == "__main__":
    argv = sys.argv[1:]
    parser = get_parser()
    args = parser.parse_args(argv)
    set_debugging(args.debug, args.logfile)
    server = WebSocketServer(
        (args.ipaddr, args.port),
        Resource({'/': RackApplication}))
    server.serve_forever()

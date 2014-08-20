#!/usr/bin/python
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
import time
import logging
import sys

ws_dict = {}

class RackApplication(WebSocketApplication):
    def on_open(self):
        pid = self.ws.environ.get("HTTP_PID")
        path = self.ws.environ.get("PATH_INFO")
        if pid and path == "/receive":
            ws_dict[pid] = self.ws
        msg = "Connection opened " + pid
        logging.debug(msg)

    def on_message(self, message):
        if self.ws.environ:
            pid = self.ws.environ.get("HTTP_PID")
            path = self.ws.environ.get("PATH_INFO")
            if path == "/send":
                receive_ws = ws_dict.get(pid)
            if receive_ws:
                msg = "Message:" + message
                logging.debug(msg)
                receive_ws.send(message)
            else:
                print "No receiver" + pid
        self.ws.close()

    def on_close(self, reason):
        print reason
        logging.debug(reason)


if __name__ == "__main__":
    argvs = sys.argv
    argc = len(argvs)
    port = int(argvs[1])
    if 2 != argc:
        print "No argment [IPC_PORT]"
        quit()
    WebSocketServer(('', port),Resource({'/': RackApplication})).serve_forever()

import websocket
import logging
import requests
from websocket import create_connection


class Receiver(object):
    def __init__(self, rack_endpoint, gid, ws_endpoint, rack_username, rack_tenant_name):
        self.rack_endpoint = rack_endpoint
        self.gid = gid
        self.ws_endpoint = ws_endpoint
        self.rack_username = rack_username
        self.rack_tenant_name = rack_tenant_name

    def receive(self, header):
        ws_url = self.ws_endpoint + "/receive"
        logging.info(ws_url)
        ws = websocket.WebSocketApp(
            ws_url,
            header=["PID:" + header],
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close)
        
        logging.info("Header: " + ws.header[0])
        logging.info("URL: " + ws.url)
        ws.run_forever()

    def on_message(self, ws, message):
        logging.info("Received message %s" % message)
        logging.info("Delete process %s" % message)
        self.delete_process(message)

    def on_error(self, ws, error):
        logging.error(error)
        ws.close()
    
    def on_close(self, ws):
        logging.info("websocket connection %s closed" % ws.header[0])

    def delete_process(self, pid):
        url = self.rack_endpoint + "/groups/" + self.gid + "/processes/" + pid
        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "X-Auth-Token": ":".join([self.rack_username, self.rack_tenant_name])
        }
        res = requests.delete(url, headers=headers)
        if res.status_code != 204:
            logging.error(res.json())
            return
        logging.info("Deleted process %s" % pid)


def send(ws_endpoint, header, message):
    ws_url = ws_endpoint + "/send"
    ws = create_connection(ws_url, header=["PID:" + header])
    ws.send(message)
    msg = "Sent message: " + message + " to connection PID:" + header
    logging.info(msg)

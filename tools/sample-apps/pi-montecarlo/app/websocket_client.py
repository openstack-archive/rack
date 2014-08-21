# Copyright (c) 2014 ITOCHU Techno-Solutions Corporation.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import websocket
import logging

logging.basicConfig(level=logging.ERROR)


class websocket_client_receive(object):

    def receive(self, ip, port, pid, message_hundler):
        ws_url = "ws://" + ip + ":" + port + "/receive"
        ws = websocket.WebSocketApp(
            ws_url,
            header=["PID: " + pid],
            on_message=message_hundler.on_message,
            on_error=self.on_error,
            on_close=self.on_close)
        ws.run_forever()

    def on_message(self, ws, message):
        msg = "Received message:" + message
        print msg
        ws.close()

    def on_error(self, ws, error):
        logging.error(error)

    def on_close(self, ws):
        logging.debug("websocket connection closed")


class websocket_client_send(object):

    def send(self, ip, port, send_pid, message):
        ws_url = "ws://" + ip + ":" + port + "/send"
        ws = websocket.create_connection(ws_url, header=["pid: " + send_pid])
        ws.send(message)
        msg = "Send message:" + message + " pid:" + send_pid
        logging.debug(msg)

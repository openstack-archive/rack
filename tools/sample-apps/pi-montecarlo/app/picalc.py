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

from math import acos
from math import fabs
from random import random
from random import seed

import datetime
import sys
import websocket_client


class PiCalcReceiver():

    def __init__(self, ip, port, pid, process_num, trials):
        self.ip = ip
        self.port = port
        self.pid = pid
        self.trials = long(trials)
        self.process_cnt = 0
        self.all_process_num = int(process_num)
        self.results = []
        self.start = _get_time()


    def on_message(self, ws, message):
        self.results.append(float(message))
        self.process_cnt += 1
        if self.process_cnt == self.all_process_num:
            self.end = _get_time()
            self._sum_by_monte_calro_method()
            _print_report(
                self.trials, self.all_process_num, self.within_circle_num,
                self.result, self.start, self.end)
            ws.close()


    def _sum_by_monte_calro_method(self):
        self.within_circle_num = sum(self.results)
        self.result = 4 * (self.within_circle_num / float(self.trials))
        return self.result


class PiCalcSender():

    def __init__(self, ip, port, pid, trials):
        self.ip = ip
        self.port = port
        self.pid = pid
        self.trials = long(trials)
        self.result = 0.0

    def count_within_circle_by_monte_carlo_method(self):
        self.result = count_within_circle_by_monte_carlo_method(self.trials)
        self._send_result()

    def _send_result(self):
        ws = websocket_client.websocket_client_send()
        ws.send(ip=self.ip, port=self.port,
                send_pid=self.pid, message=str(self.result))


def _get_time():
    return datetime.datetime.now()


def count_within_circle_by_monte_carlo_method(trials):
    seed()
    n = 0.0
    for i in xrange(trials):
        x = random()
        y = random()
        if (x ** 2 + y ** 2 < 1):
            n += 1
    return n


def calc_by_monte_carlo_method(trials):
    start = _get_time()
    seed()
    n = 0.0
    for i in xrange(trials):
        x = random()
        y = random()
        if (x ** 2 + y ** 2 < 1):
            n += 1
    result = 4 * (n / trials)
    end = _get_time()
    _print_report(trials, 1, n, result, start, end)


def _print_report(trials, process_num, within_circle_num, result, start, end):

    report = \
    "------------------------------------------------------------------\n" + \
    "picalc result\n" + \
    "------------------------------------------------------------------\n" + \
    " trials        : " + str(int(trials)) + "\n" + \
    " process       : " + str(int(process_num)) + "\n" + \
    " within circle : " + str(int(within_circle_num)) + "\n" + \
    "------------------------------------------------------------------\n" + \
    " pi            : " + str(acos(-1)) + "\n" \
    " result        : " + str(result) + "\n" \
    " error         : " + str(fabs(result - acos(-1))) + "\n" \
    "------------------------------------------------------------------\n" + \
    " time          : " + "%02d d %02d h %02d m %02d s" % \
                                _calc_time_diff(start, end) + "\n" \
    "------------------------------------------------------------------\n"
    print report
    f = open('picalc_result', 'w')
    f.write(report)
    f.close()


def _calc_time_diff(start, end):
    t = end - start
    return (t.days, t.seconds / 3600, t.seconds / 60, t.seconds % 60)


def _calc_time_diff_by_sec(start, end):
    t = end - start
    return str(t.days * 3600 * 24 + t.seconds)


def _receiver_main(argvs):
    receiver = PiCalcReceiver(argvs[2], argvs[3], argvs[4], argvs[5], argvs[6])
    ws = websocket_client.websocket_client_receive()
    ws.receive(ip=receiver.ip,
               port=receiver.port,
               pid=receiver.pid,
               message_hundler=receiver)


def _sender_main(argvs):
    sender = PiCalcSender(argvs[2], argvs[3], argvs[4], argvs[5])
    sender.count_within_circle_by_monte_carlo_method()


def main():
    argvs = sys.argv
    argc = len(argvs)

    if (argc < 2):
        print 'Usage: picalc.py [[receiver|sender] proxy_ip proxy_port pid '\
              '[receiver:number_of_process]] number_of_trials'
        quit()
    if (argvs[1] == "receiver"):
        _receiver_main(argvs)
    elif (argvs[1] == "sender"):
        _sender_main(argvs)
    else:
        calc_by_monte_carlo_method(long(argvs[1]))


if __name__ == "__main__":
    main()

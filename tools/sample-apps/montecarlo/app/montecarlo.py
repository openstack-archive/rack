#!/usr/bin/env python

import logging
import random
import sys
import traceback
import prettytable
from math import acos, fabs
from rackclient import process_context
from rackclient.v1.syscall.default import syscall, signal
from rackclient.v1.syscall.default.pipe import EndOfFile
import time

PCTXT = process_context.PCTXT

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s - %(message)s %(filename)s:%(lineno)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
LOG = logging.getLogger(__name__)


def parent(trials, workers, stdout):
    trials = int(trials)
    workers = int(workers)
    if workers > trials:
        raise Exception("'trials' must be larger than 'workers'.")

    t1 = time.time()
    LOG.debug("Start time: %s", t1)

    p = syscall.pipe()

    trials_per_child = trials / workers
    remainder = trials % workers
    LOG.debug("Trials per child: %s", trials_per_child)
    LOG.debug("Remainder: %s", remainder)

    pids = []
    for i in range(0, workers):
        args = {"trials": trials_per_child}
        if i == 0:
            args["trials"] += remainder
        child = syscall.fork(args=args)
        LOG.debug("Fork a child: %s", child.pid)
        pids.append(child.pid)

    p.close_writer()

    ws = signal.SignalManager()
    ws.pids = pids

    def _on_message(message):
        try:
            ws.pids.remove(message)
        except:
            pass
        if len(ws.pids) == 0:
            return True

    LOG.debug("Waits for messages...")
    ws.receive(_on_message)

    LOG.debug("Reads pipe")
    points = 0
    try:
        while True:
            point = p.read()
            points += int(point)
    except EndOfFile:
        p.close_reader()

    t2 = time.time()
    LOG.debug("End time: %s", t2)
    exec_time = str(t2-t1)
    LOG.debug("Exec time: %s", exec_time)

    report_string = make_report(trials, workers, points, exec_time)
    LOG.debug(report_string)

    path = stdout.lstrip('/').split('/', 1)
    f = syscall.fopen(path[0], path[1], 'w')
    f.write(report_string)
    f.close()

    LOG.debug("Kill myself")
    PCTXT.client.processes.delete(PCTXT.gid, PCTXT.pid)


def make_report(trials, workers, points, time):
    result = 4 * float(points) / float(trials)

    pt = prettytable.PrettyTable(['Property', 'Value'])
    pt.align = 'l'
    pt.add_row(['trials', trials])
    pt.add_row(['workers', workers])
    pt.add_row(['points', points])
    pt.add_row(['pi', acos(-1)])
    pt.add_row(['result', result])
    pt.add_row(['error', fabs(result - acos(-1))])
    pt.add_row(['time', time])

    return pt.get_string()


def child(trials):
    trials = int(trials)
    
    p = syscall.pipe()
    p.close_reader()

    LOG.debug("Start trials")
    points = 0
    for i in xrange(trials):
        x = random.random()
        y = random.random()
        if (x ** 2 + y ** 2) <= 1:
            points += 1
    LOG.debug("Total points: %s", points)

    p.write(str(points))
    p.close_writer()

    ws = signal.SignalManager()
    LOG.debug("Send a signal to the parent process")
    ws.send(target_id=PCTXT.ppid, message=PCTXT.pid)


def main():
    trials = getattr(PCTXT, 'trials', None)
    workers = getattr(PCTXT, 'workers', None)
    stdout = getattr(PCTXT, 'stdout', None)

    ppid = getattr(PCTXT, 'ppid', None)
    if not ppid:
        if not trials and not workers and not stdout:
            msg = "Parent process needs the options, 'trials' and 'workers'."
            LOG.debug(msg)
            raise Exception(msg)
        parent(trials, workers, stdout)
    else:
        if not trials:
            msg = "Child process needs the option 'trials'."
            LOG.debug(msg)
            raise Exception(msg)
        child(trials)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        LOG.exception(e)
        PCTXT.client.processes.update(PCTXT.gid, PCTXT.pid, traceback.format_exc())
        sys.exit(1)

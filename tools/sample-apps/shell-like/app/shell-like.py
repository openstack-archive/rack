import logging
import sys
import uuid
import traceback
import subprocess
import shlex

from rackclient import process_context
from rackclient.v1.syscall.default import syscall
from rackclient.v1.syscall.default import pipe as rackpipe, file as rackfile, signal

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s - %(message)s %(filename)s:%(lineno)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
LOG = logging.getLogger(__name__)

PCTXT = process_context.PCTXT


def parse_command(command):
    """
    :param command: shell command
    :return: list of commands

    Example
    command: grep ^example.*$ | sed -e "s/test/test2/"
    return: [['grep', '^example.*$], ['sed', '-e', 's/test/test2/']]
    """
    l = shlex.split(str(command))
    cmds = []
    while l:
        try:
            cmds.append(l[0:l.index('|')])
            del l[0:l.index('|') + 1]
        except ValueError:
            cmds.append(l[0:])
            break
    return cmds


def boot_cluster(cmd_list, input, output):
    """
    :param cmd_list: value from parse_command()
    :param input: list of file names
    :param output: list of file names

    Example
    boot a cluster of processes with args like following.
    cmd_list: [['grep', '^example.*$], ['sed', '-e', 's/test/test2/']]
    args of process1: {"command": "grep ^example.*$", "stdin": "/input/file1,/input/file2", "stdout": "pipe-UUID,pipe-UUID"}
    args of process2: {"command": "sed -e s/test/test2/", "stdin": "pipe-UUID,pipe-UUID", "stdout": "/output/file1,/output/file2"}
    """
    cmds = cmd_list[:]
    file_num = len(input)
    pipe_num = (len(cmds) - 1) * file_num
    pipes = ['pipe-' + str(uuid.uuid4()) for i in range(pipe_num)]
    pids = []

    j = 0
    for i in range(len(cmds)):
        args = dict(command=' '.join(cmds[i]))

        # the first process of a cluster
        if i == 0:
            args["stdin"] = ','.join(input)
        else:
            args["stdin"] = ','.join(pipes[j:j+file_num])
            j += file_num
        # the last process of a cluster
        if i == len(cmds) - 1:
            args["stdout"] = ','.join(output)
        else:
            args["stdout"] = ','.join(pipes[j:j+file_num])

        LOG.debug("Boot a process with args: %s", args)
        child = syscall.fork(args=args)
        LOG.debug("Forked a child %s", child.pid)
        pids.append(child.pid)
    return pids


def parse_io(stdin, stdout):
    """
    :param stdin: comma separated string such as '/input/file1,/input/file2' and 'pipe-UUID,pipe-UUID'
    :param stdout: comma separated string such as '/output/file1,/output/file2' and 'pipe-UUID,pipe-UUID'
    :return: list of file objects or list of rack pipe objects
    """
    in_list = stdin.split(',')
    out_list = stdout.split(',')

    if in_list[0][0:5] == 'pipe-':
        input = []
        for i in in_list:
            p = syscall.pipe(i)
            p.close_writer()
            input.append(p)
    else:
        path_list = [x.strip('/').split('/', 1) for x in in_list]
        input = [syscall.fopen(x[0], x[1], 'r') for x in path_list]

    if out_list[0][0:5] == 'pipe-':
        output = []
        for i in out_list:
            p = syscall.pipe(i)
            p.close_reader()
            output.append(p)
    else:
        path_list = [x.strip('/').split('/', 1) for x in out_list]
        output = [syscall.fopen(p[0], p[1], 'w') for p in path_list]

    return input, output


def execute_shell(command, input, output):
    """
    :param command: shell command
    :param input: list of file objects or list of rack pipe objects
    :param output: list of file objects or list of rack pipe objects
    """
    for i in range(len(input)):
        # from file to file
        if isinstance(input[i], rackfile.File) and isinstance(output[i], rackfile.File):
            p = subprocess.Popen(command, stdin=input[i], stdout=subprocess.PIPE, shell=True)
            output[i].write(p.communicate()[0])
            output[i].close()
        # from file to pipe
        elif isinstance(input[i], rackfile.File) and isinstance(output[i], rackpipe.Pipe):
            p = subprocess.Popen(command, stdin=input[i], stdout=subprocess.PIPE, shell=True)
            output[i].write(p.communicate()[0])
            output[i].close_writer()
        # from pipe to pipe
        elif isinstance(input[i], rackpipe.Pipe) and isinstance(output[i], rackpipe.Pipe):
            try:
                while True:
                    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
                    output[i].write(p.communicate(input=input[i].read())[0])
            except rackpipe.EndOfFile:
                input[i].close_reader()
                output[i].close_writer()
        # from pipe to file
        elif isinstance(input[i], rackpipe.Pipe) and isinstance(output[i], rackfile.File):
            try:
                while True:
                    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
                    output[i].write(p.communicate(input=input[i].read())[0])
                    output[i].close()
            except rackpipe.EndOfFile:
                input[i].close_reader()


def parent(command, stdin, stdout, cluster):
    cluster = int(cluster)

    input_path = stdin.strip('/').split('/', 1)
    output_path = stdout.strip('/').split('/', 1)
    filename_list = rackfile.get_objects(input_path[0])
    file_per_cluster = len(filename_list) / cluster
    remainder = len(filename_list) % cluster

    cmds = parse_command(command)
    LOG.debug("Parsed command: %s", cmds)

    i = 0
    while i != len(filename_list):
        if i == 0:
            files = filename_list[i:i + file_per_cluster + remainder]
            i += file_per_cluster + remainder
        else:
            files = filename_list[i:i + file_per_cluster]
            i += file_per_cluster
        # like ['/input/file1', '/input/file2']
        input = ['/' + input_path[0]  + '/' + f for f in files]
        # like ['/output/file1', '/output/file2']
        output = ['/' + output_path[0] + '/' + f for f in files]
        pids = boot_cluster(cmds, input, output)

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

    LOG.debug("Kill myself")
    PCTXT.client.processes.delete(PCTXT.gid, PCTXT.pid)


def child(command, stdin, stdout):
    input, output = parse_io(stdin, stdout)
    execute_shell(command, input, output)

    ws = signal.SignalManager()
    LOG.debug("Send a signal to the parent process")
    ws.send(target_id=PCTXT.ppid, message=PCTXT.pid)


def main():
    command = getattr(PCTXT, 'command', None)
    stdin = getattr(PCTXT, 'stdin', None)
    stdout = getattr(PCTXT, 'stdout', None)
    cluster = getattr(PCTXT, 'cluster', None)

    if not command and not stdin and not stdout:
        msg = "You must provide the options, 'command', 'stdin' and 'stdout'."
        LOG.debug(msg)
        raise Exception(msg)

    ppid = getattr(PCTXT, 'ppid', None)
    if not ppid:
        if not cluster:
            msg = "You must provide the option 'cluster'."
            LOG.debug(msg)
            raise Exception(msg)
        parent(command, stdin, stdout, cluster)
    else:
        child(command, stdin, stdout)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        LOG.exception(e)
        PCTXT.client.processes.update(PCTXT.gid, PCTXT.pid, traceback.format_exc())
        sys.exit(1)

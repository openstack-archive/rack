import os
import sys

from novaclient import client

def get_rackapi_addr():
    VERSION = 2
    username = sys.argv[1]
    password = sys.argv[2]
    project_id = sys.argv[3]
    auth_url = sys.argv[4]

    nova = client.Client(VERSION, username, password, project_id, auth_url)
    servers = nova.servers.list()
    api_servers = filter(lambda s: s.metadata.get("role") == 'api', servers)
    server = api_servers[0]
    addr = None
    for key in server.addresses.keys():
        for address in server.addresses[key]:
            addr = address["addr"]
    return addr

if __name__ == '__main__':
    print get_rackapi_addr()

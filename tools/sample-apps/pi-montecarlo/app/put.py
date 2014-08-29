import os
import sys
from swiftclient import client as swift_client


def main():
    argvs = sys.argv
    argc = len(argvs)

    if (argc < 2):
        print 'Usage: put.py container_name put_file_path'
        quit()

    client = swift_client.Connection(user=os.getenv("OS_USERNAME"),
                                     key=os.getenv("OS_PASSWORD"),
                                     tenant_name=os.getenv("OS_TENANT_NAME"),
                                     authurl=os.getenv("OS_AUTH_URL"),
                                     auth_version="2")

    f = open(argvs[2])
    data = f.read()
    client.put_object(argvs[1], "result.txt", data)

if __name__ == "__main__":
    main()

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
#!/usr/bin/env python

import argparse
import json
import os
import requests
import sys
import logging

from keystoneclient.v2_0 import client as keystone_client


def get_parser():
    parser = argparse.ArgumentParser(description="rack client")
    parser.add_argument("--noauth", action="store_false", help="request without auth")
    parser.add_argument("--os-username", default=os.getenv("OS_USERNAME"), help="")
    parser.add_argument("--os-password", default=os.getenv("OS_PASSWORD"), help="")
    parser.add_argument("--os-tenant_name", default=os.getenv("OS_TENANT_NAME"), help="")
    parser.add_argument("--os-auth_url", default=os.getenv("OS_AUTH_URL"), help="")

    parser.add_argument("--debug", action="store_true", help="print debugging output")
    parser.add_argument("--url", default="http://localhost:8088/v1/", help="rack-api endpoint")
    subparsers = parser.add_subparsers(help="commands")

    #group list
    group_list_parser = subparsers.add_parser("group-list", help="list groups")
    group_list_parser.set_defaults(func=group_list)

    #group show
    group_list_parser = subparsers.add_parser("group-show", help="list group details")
    group_list_parser.add_argument("--gid", action="store", required=True)
    group_list_parser.set_defaults(func=group_show)

    #group create
    group_create_parser = subparsers.add_parser("group-create", help="create group")
    group_create_parser.add_argument("--name", action="store")
    group_create_parser.add_argument("--description", action="store")
    group_create_parser.set_defaults(func=group_create)

    #group update
    group_create_parser = subparsers.add_parser("group-update", help="update group")
    group_create_parser.add_argument("--gid", action="store", required=True)
    group_create_parser.add_argument("--name", action="store")
    group_create_parser.add_argument("--description", action="store")
    group_create_parser.set_defaults(func=group_update)

    #group delete
    group_delete_parser = subparsers.add_parser("group-delete", help="delete group")
    group_delete_parser.add_argument("--gid", action="store", required=True)
    group_delete_parser.set_defaults(func=group_delete)

    #keypair list
    keypair_list_parser = subparsers.add_parser("keypair-list", help="list keypairs")
    keypair_list_parser.add_argument("--gid", action="store", required=True)
    keypair_list_parser.set_defaults(func=keypair_list)

    #keypair show
    keypair_show_parser = subparsers.add_parser("keypair-show", help="list keypair details")
    keypair_show_parser.add_argument("--gid", action="store", required=True)
    keypair_show_parser.add_argument("--keypair_id", action="store", required=True)
    keypair_show_parser.set_defaults(func=keypair_show)

    #keypair create
    keypair_create_parser = subparsers.add_parser("keypair-create", help="create keypair")
    keypair_create_parser.add_argument("--gid", action="store", required=True)
    keypair_create_parser.add_argument("--name", action="store")
    keypair_create_parser.add_argument("--is_default", action="store")
    keypair_create_parser.set_defaults(func=keypair_create)

    #keypair update
    keypair_update_parser = subparsers.add_parser("keypair-update", help="update keypair")
    keypair_update_parser.add_argument("--gid", action="store", required=True)
    keypair_update_parser.add_argument("--keypair_id", action="store", required=True)
    keypair_update_parser.add_argument("--is_default", action="store", required=True)
    keypair_update_parser.set_defaults(func=keypair_update)

    #keypair delete
    keypair_delete_parser = subparsers.add_parser("keypair-delete", help="delete keypair")
    keypair_delete_parser.add_argument("--gid", action="store", required=True)
    keypair_delete_parser.add_argument("--keypair_id", action="store", required=True)
    keypair_delete_parser.set_defaults(func=keypair_delete)

    #securitygroup list
    securitygroup_list_parser = subparsers.add_parser("securitygroup-list", help="list securitygroups")
    securitygroup_list_parser.add_argument("--gid", action="store", required=True)
    securitygroup_list_parser.set_defaults(func=securitygroup_list)

    #securitygroup show
    securitygroup_show_parser = subparsers.add_parser("securitygroup-show", help="list securitygroup details")
    securitygroup_show_parser.add_argument("--gid", action="store", required=True)
    securitygroup_show_parser.add_argument("--securitygroup_id", action="store", required=True)
    securitygroup_show_parser.set_defaults(func=securitygroup_show)

    #securitygroup create
    securitygroup_create_parser = subparsers.add_parser("securitygroup-create", help="create securitygroup")
    securitygroup_create_parser.add_argument("--gid", action="store", required=True)
    securitygroup_create_parser.add_argument("--name", action="store")
    securitygroup_create_parser.add_argument("--is_default", action="store")
    securitygroup_create_parser.add_argument("--securitygrouprules", metavar="key1=value1[,key2=value2...]", action="store", nargs="+", default=[])
    securitygroup_create_parser.set_defaults(func=securitygroup_create)

    #securitygroup update
    securitygroup_update_parser = subparsers.add_parser("securitygroup-update", help="update securitygroup")
    securitygroup_update_parser.add_argument("--gid", action="store", required=True)
    securitygroup_update_parser.add_argument("--securitygroup_id", action="store", required=True)
    securitygroup_update_parser.add_argument("--is_default", action="store", required=True)
    securitygroup_update_parser.set_defaults(func=securitygroup_update)

    #securitygroup delete
    securitygroup_delete_parser = subparsers.add_parser("securitygroup-delete", help="delete securitygroup")
    securitygroup_delete_parser.add_argument("--gid", action="store", required=True)
    securitygroup_delete_parser.add_argument("--securitygroup_id", action="store", required=True)
    securitygroup_delete_parser.set_defaults(func=securitygroup_delete)

    #network list
    network_list_parser = subparsers.add_parser("network-list", help="list networks")
    network_list_parser.add_argument("--gid", action="store", required=True)
    network_list_parser.set_defaults(func=network_list)

    #network show
    network_show_parser = subparsers.add_parser("network-show", help="list network details")
    network_show_parser.add_argument("--gid", action="store", required=True)
    network_show_parser.add_argument("--network_id", action="store", required=True)
    network_show_parser.set_defaults(func=network_show)

    #network create
    network_create_parser = subparsers.add_parser("network-create", help="create network")
    network_create_parser.add_argument("--gid", action="store", required=True)
    network_create_parser.add_argument("--name", action="store")
    network_create_parser.add_argument("--cidr", action="store", required=True)
    network_create_parser.add_argument("--is_admin", action="store")
    network_create_parser.add_argument("--gateway", action="store")
    network_create_parser.add_argument("--dns_nameservers", action="store", nargs="+")
    network_create_parser.add_argument("--ext_router_id", action="store")
    network_create_parser.set_defaults(func=network_create)

    #network update
    network_update_parser = subparsers.add_parser("network-update", help="update network")
    network_update_parser.add_argument("--gid", action="store", required=True)
    network_update_parser.add_argument("--network_id", action="store", required=True)
    network_update_parser.add_argument("--is_admin", action="store", required=True)
    network_update_parser.set_defaults(func=network_update)

    #network delete
    network_delete_parser = subparsers.add_parser("network-delete", help="delete network")
    network_delete_parser.add_argument("--gid", action="store", required=True)
    network_delete_parser.add_argument("--network_id", action="store", required=True)
    network_delete_parser.set_defaults(func=network_delete)

    #process list
    process_list_parser = subparsers.add_parser("process-list", help="list processes")
    process_list_parser.add_argument("--gid", action="store", required=True)
    process_list_parser.set_defaults(func=process_list)

    #process show
    process_show_parser = subparsers.add_parser("process-show", help="list process details")
    process_show_parser.add_argument("--gid", action="store", required=True)
    process_show_parser.add_argument("--pid", action="store", required=True)
    process_show_parser.set_defaults(func=process_show)

    #process create
    process_create_parser = subparsers.add_parser("process-create", help="create process")
    process_create_parser.add_argument("--gid", action="store", required=True)
    process_create_parser.add_argument("--name", action="store")
    process_create_parser.add_argument("--ppid", action="store")
    process_create_parser.add_argument("--nova_flavor_id", action="store")
    process_create_parser.add_argument("--glance_image_id", action="store")
    process_create_parser.add_argument("--keypair_id", action="store")
    process_create_parser.add_argument("--securitygroup_ids", action="store", nargs="+")
    process_create_parser.add_argument("--userdata", metavar="\"Customization Script...(must be base64 encoded)\"", action="store")
    process_create_parser.add_argument("--args", metavar="key1=value1[,key2=value2...]", action="store")
    process_create_parser.set_defaults(func=process_create)

    #process delete
    process_delete_parser = subparsers.add_parser("process-delete", help="delete process")
    process_delete_parser.add_argument("--gid", action="store", required=True)
    process_delete_parser.add_argument("--pid", action="store", required=True)
    process_delete_parser.set_defaults(func=process_delete)

    #process update
    process_update_parser = subparsers.add_parser("process-update", help="update process")
    process_update_parser.add_argument("--gid", action="store", required=True)
    process_update_parser.add_argument("--pid", action="store", required=True)
    process_update_parser.add_argument("--app_status", action="store", required=True)
    process_update_parser.set_defaults(func=process_update)

    #proxy show
    proxy_show_parser = subparsers.add_parser("proxy-show", help="list proxy details")
    proxy_show_parser.add_argument("--gid", action="store", required=True)
    proxy_show_parser.set_defaults(func=proxy_show)

    #proxy create
    proxy_create_parser = subparsers.add_parser("proxy-create", help="create proxy")
    proxy_create_parser.add_argument("--gid", action="store", required=True)
    proxy_create_parser.add_argument("--name", action="store")
    proxy_create_parser.add_argument("--nova_flavor_id", action="store")
    proxy_create_parser.add_argument("--glance_image_id", action="store")
    proxy_create_parser.add_argument("--keypair_id", action="store")
    proxy_create_parser.add_argument("--securitygroup_ids", action="store", nargs="+")
    proxy_create_parser.add_argument("--userdata", metavar="\"Customization Script...(must be base64 encoded)\"", action="store")
    proxy_create_parser.add_argument("--args", metavar="key1=value1[,key2=value2...] value_separator:'/'", action="store")
    proxy_create_parser.set_defaults(func=proxy_create)

    #proxy update
    proxy_update_parser = subparsers.add_parser("proxy-update", help="update proxy")
    proxy_update_parser.add_argument("--gid", action="store", required=True)
    proxy_update_parser.add_argument("--shm_endpoint", action="store", required=False)
    proxy_update_parser.add_argument("--ipc_endpoint", action="store", required=False)
    proxy_update_parser.add_argument("--fs_endpoint", action="store", required=False)
    proxy_update_parser.add_argument("--app_status", action="store", required=False)
    proxy_update_parser.set_defaults(func=proxy_update)

    return parser


def group_list(args, headers):
    url = args.url + "groups"
    return requests.get(url, headers=headers)


def group_show(args, headers):
    url = args.url + "groups/" + args.gid
    return requests.get(url, headers=headers)


def group_create(args, headers):
    url = args.url + "groups"

    payload = {}
    if not args.name:
        sys.exit("name is required.")
    payload["name"] = args.name
    if args.description:
        payload["description"] = args.description
    data = json.dumps(dict(group=payload))

    return requests.post(url, data=data, headers=headers)


def group_update(args, headers):
    url = args.url + "groups/" + args.gid

    payload = {}
    if args.name:
        payload["name"] = args.name
    if args.description:
        payload["description"] = args.description
    if not payload:
        sys.exit("No attribute is provided.")
    data = json.dumps(dict(group=payload))

    return requests.put(url, data=data, headers=headers)


def group_delete(args, headers):
    url = args.url + "groups/" + args.gid
    return requests.delete(url, headers=headers)


def keypair_list(args, headers):
    url = args.url + "groups/" + args.gid + "/keypairs"
    return requests.get(url, headers=headers)


def keypair_show(args, headers):
    url = args.url + "groups/" + args.gid + "/keypairs/" + args.keypair_id
    return requests.get(url, headers=headers)


def keypair_create(args, headers):
    url = args.url + "groups/" + args.gid + "/keypairs"

    payload = {}
    if args.name:
        payload["name"] = args.name
    if args.is_default:
        payload["is_default"] = args.is_default
    data = json.dumps(dict(keypair=payload))

    return requests.post(url, data=data, headers=headers)


def keypair_update(args, headers):
    url = args.url + "groups/" + args.gid + "/keypairs/" + args.keypair_id

    payload = {}
    payload["is_default"] = args.is_default
    data = json.dumps(dict(keypair=payload))

    return requests.put(url, data=data, headers=headers)


def keypair_delete(args, headers):
    url = args.url + "groups/" + args.gid + "/keypairs/" + args.keypair_id
    return requests.delete(url, headers=headers)


def securitygroup_list(args, headers):
    url = args.url + "groups/" + args.gid + "/securitygroups"
    return requests.get(url, headers=headers)


def securitygroup_show(args, headers):
    url = args.url + "groups/" + args.gid + "/securitygroups/" + args.securitygroup_id
    return requests.get(url, headers=headers)


def securitygroup_create(args, headers):
    url = args.url + "groups/" + args.gid + "/securitygroups"

    payload = {}
    if args.name:
        payload["name"] = args.name
    if args.is_default:
        payload["is_default"] = args.is_default
    securitygrouprules = []
    for rule_params in args.securitygrouprules:
        rule_dict = dict(v.split("=") for v in rule_params.split(","))
        securitygrouprules.append(rule_dict)
    payload["securitygrouprules"] = securitygrouprules
    data = json.dumps(dict(securitygroup=payload))

    return requests.post(url, data=data, headers=headers)


def securitygroup_update(args, headers):
    url = args.url + "groups/" + args.gid + "/securitygroups/" + args.securitygroup_id

    payload = {}
    payload["is_default"] = args.is_default
    data = json.dumps(dict(securitygroup=payload))

    return requests.put(url, data=data, headers=headers)


def securitygroup_delete(args, headers):
    url = args.url + "groups/" + args.gid + "/securitygroups/" + args.securitygroup_id
    return requests.delete(url, headers=headers)


def network_list(args, headers):
    url = args.url + "groups/" + args.gid + "/networks"
    return requests.get(url, headers=headers)


def network_show(args, headers):
    url = args.url + "groups/" + args.gid + "/networks/" + args.network_id
    return requests.get(url, headers=headers)


def network_create(args, headers):
    url = args.url + "groups/" + args.gid + "/networks"

    payload = {}
    if args.name:
        payload["name"] = args.name
    if args.cidr:
        payload["cidr"] = args.cidr
    if args.is_admin:
        payload["is_admin"] = args.is_admin
    if args.gateway:
        payload["gateway"] = args.gateway
    if args.dns_nameservers:
        payload["dns_nameservers"] = args.dns_nameservers
    if args.ext_router_id:
        payload["ext_router_id"] = args.ext_router_id
    data = json.dumps(dict(network=payload))

    return requests.post(url, data=data, headers=headers)


def network_update(args, headers):
    url = args.url + "groups/" + args.gid + "/networks/" + args.network_id

    payload = {}
    payload["is_admin"] = args.is_admin
    data = json.dumps(dict(network=payload))

    return requests.put(url, data=data, headers=headers)


def network_delete(args, headers):
    url = args.url + "groups/" + args.gid + "/networks/" + args.network_id
    return requests.delete(url, headers=headers)


def process_list(args, headers):
    url = args.url + "groups/" + args.gid + "/processes"
    return requests.get(url, headers=headers)


def process_show(args, headers):
    url = args.url + "groups/" + args.gid + "/processes/" + args.pid
    return requests.get(url, headers=headers)


def process_create(args, headers):
    url = args.url + "groups/" + args.gid + "/processes"

    payload = {}
    if args.name:
        payload["name"] = args.name
    if args.ppid:
        payload["ppid"] = args.ppid
    if args.keypair_id:
        payload["keypair_id"] = args.keypair_id
    if args.nova_flavor_id:
        payload["nova_flavor_id"] = args.nova_flavor_id
    if args.glance_image_id:
        payload["glance_image_id"] = args.glance_image_id
    if args.securitygroup_ids:
        payload["securitygroup_ids"] = args.securitygroup_ids
    if args.args:
        payload["args"] = dict(v.split("=", 1) for v in args.metadata.split(","))
    if args.userdata:
        payload["userdata"] = args.userdata
    data = json.dumps(dict(process=payload))

    return requests.post(url, data=data, headers=headers)


def process_update(args, headers):
    url = args.url + "groups/" + args.gid + "/processes/" + args.pid

    payload = {}
    payload["app_status"] = args.app_status
    data = json.dumps(dict(process=payload))

    return requests.put(url, data=data, headers=headers)


def process_delete(args, headers):
    url = args.url + "groups/" + args.gid + "/processes/" + args.pid
    return requests.delete(url, headers=headers)


def proxy_show(args, headers):
    url = args.url + "groups/" + args.gid + "/proxy"
    return requests.get(url, headers=headers)


def proxy_create(args, headers):
    url = args.url + "groups/" + args.gid + "/proxy"

    payload = {}
    if args.name:
        payload["name"] = args.name
    if args.keypair_id:
        payload["keypair_id"] = args.keypair_id
    if args.nova_flavor_id:
        payload["nova_flavor_id"] = args.nova_flavor_id
    if args.glance_image_id:
        payload["glance_image_id"] = args.glance_image_id
    if args.securitygroup_ids:
        payload["securitygroup_ids"] = args.securitygroup_ids
    if args.userdata:
        payload["userdata"] = args.userdata
    if args.args:
        payload["args"] = dict(v.split("=", 1) for v in args.metadata.split(","))
    data = json.dumps(dict(proxy=payload))

    return requests.post(url, data=data, headers=headers)

def proxy_update(args, headers):
    url = args.url + "groups/" + args.gid + "/proxy"

    payload = {}
    payload["shm_endpoint"] = args.shm_endpoint
    payload["ipc_endpoint"] = args.ipc_endpoint
    payload["fs_endpoint"] = args.fs_endpoint
    payload["app_status"] = args.app_status
    data = json.dumps(dict(proxy=payload))

    return requests.put(url, data=data, headers=headers)

def main():
    parser = get_parser()
    args = parser.parse_args()

    if args.noauth:
        if not args.os_username or not args.os_tenant_name:
            sys.exit("You must provide --os-username or env[OS_USERNAME], --os-tenant_name or env[OS_TENANT_NAME]")
        token = ":".join([args.os_username, args.os_tenant_name])
    else:
        if not args.os_username or not args.os_password\
                or not args.os_tenant_name or not args.os_auth_url:
            sys.exit("You must provide --os-username or env[OS_USERNAME], "
                     "--os-password or env[OS_PASSWORD], --os-tenant_name or env[OS_TENANT_NAME], "
                     "and --os-auth_url or env[OS_AUTH_URL]")

        keystone = keystone_client.Client(
                            username=args.os_username,
                            password=args.os_password,
                            auth_url=args.os_auth_url,
                            tenant_name=args.os_tenant_name)
        token = keystone.auth_token

    headers = {"content-type": "application/json",
               "accept": "application/json",
               "X-Auth-Token": token}
    res = args.func(args, headers)

    print "HTTP STATUS: " + str(res.status_code)
    print json.dumps(res.json(), indent=4)


if __name__ == "__main__":
    main()

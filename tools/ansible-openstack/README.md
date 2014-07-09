OpenStack-Ansible
=================

# Description
This repository contains playbooks for installation of OpenStack Icehouse for CentOS.  
These playbooks will..
* install necessary  packages
* install MySQL, AMQP
* install Keystone, Glance, Cinder
* install Neutron (with linunxbridge, vlan, ml2 configuration)
* install Nova, Horizon
* setup provider network

These playbooks are based on [yosshy/openstack-ansible](https://github.com/yosshy/openstack-ansible) and also [utilizing openstack-ansible-modules](https://github.com/openstack-ansible/openstack-ansible-modules).


# Requirements
* Ansible 1.6 or later
* CentOS 6.5 or later
* Internet accessible network

# Assumptions of host network
We assume following three networks for OpenStack hosts.
* External network  
A network end-users access from the Internet to interact virtual instances, dashboard and api.
Also employed to network-gateway node's external link.

* Internal network  
OpenStack components talk to each other via this network.
   
* Management network  
Ansible accesses OpenStack hosts via this network.

# Before Running
### automatic ssh login
You can simply copy ssh public key to the remote node with following command.  
	ssh-copy-id root@<remoteNode>
Also specify ssh private key in ansible.cfg file.  
	private_key=/root/.ssh/id_rsa 
	ask_pass = False  
### manual ssh login(unrecommended)
Or if you don't like ssh key, comment out private_key_file=** and change ask_pass=True in ansible.cfg file.  
	# private_key_file=**  
	ask_pass = True  
	
### role of each OpenStack nodes
Determine the role of each OpenStack nodes in openstack_hosts file  
 * frontend: API, horizon
 * controller: nova-{conductor,scheduler,etc}, glance-registry, cinder-scheduler, etc.
 * network_gateway: all neutron services except neutron-server
 * volume_backend: used for cinder-volume and its LVM-based backend
 * sql_backend: used for mySql
 * amqp_backend: used for AMQP
 * compute_backend: nova-compute, neutron-agent and KVM

### system/openstack settings
Edit system/OpenStack settings in group_vars/all file.
You can set passwords, cinder volume to use, VLAN range, provider network details, etc. in this file.

### interface mapping
Determine interface mapping of External/Internal/Management for each role nodes.
Edit group_vars/{compute_backend|controller|frontend|network_gateway|volume_backend|sql_backend} and specify which interface to use for which network.




    
OpenStack-Ansible
=================

# Description
This repository contains playbooks to install the OpenStack Icehouse for CentOS.  
These playbooks will..
* install necessary  packages
* install MySQL, AMQP
* install Keystone, Glance, Cinder
* install Neutron (with linunxbridge, vlan, ml2 configuration)
* install Nova, Horizon, Heat
* setup provider network
* install Ceilometer(separate yml)

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
### Automatic ssh login
You can simply copy ssh public key to the remote node with following command.  

    ssh-copy-id root@remoteNode

Also specify ssh private key in ansible.cfg file.  

    private_key=/root/.ssh/id_rsa 
    ask_pass = False  


### Manual ssh login(unrecommended)
Or if you don't like ssh key, comment out private_key_file=** and change ask_pass=True in ansible.cfg file.  

    # private_key_file=**
    ask_pass = True
	
### Role of each OpenStack nodes
Determine the role of each OpenStack nodes in openstack_hosts file  
 * [frontend]: API, horizon
 * [controller]: nova-{conductor,scheduler,etc}, glance-registry, cinder-scheduler, etc.
 * [network_gateway]: all neutron services except neutron-server
 * [volume_backend]: used for cinder-volume and its LVM-based backend
 * [sql_backend]: used for mySql
 * [amqp_backend]: used for AMQP
 * [compute_backend]: nova-compute, neutron-agent and KVM
 * [heat_engine_backend]: openstack-heat-engine
 * [ceilometer_db_backend]: MongoDB node for Ceilometer
 * [ceilometer_controller]: ceilometer central, collector, notifier and other tools.

### system/openstack settings
Edit system/OpenStack settings in group_vars/all file.
You can set passwords, which cinder volume to use, VLAN range, provider network details, etc. in this file.

### Interface mapping
Determine interface mapping of External/Internal/Management for each role nodes.
Edit `group_vars/{everything but all}` and specify which interface to use for which network.
In default, eth1 for internal NW, eth2 for External network and eth3 for Management NW.


# How to run
Go to the directory where `set_openstack.yml` is located, and `ansible-playbook set_openstack.yml`
Or you can use Jenkins to kick playbook with following shell script.

    /usr/bin/ansible-playbook $WORKSPACE/set_openstack.yml

After set_openstack.yml is completed, you can install ceilometer additionally.

    /usr/bin/ansible-playbook $WORKSPACE/set_ceilometer.yml

***
## Tips: faster installation
You can pick up your own repositories to install faster.
Place your repository files in `templates/etc/yum.repos.d` directory and set `use_your_own_repository true` in `group_vars/all`.

## Tips: Cinder volume
You can use a loop back device for cinder volume instead of the whole disk.

    losetup --find
    dd if=/dev/zero of=/var/lib/disk.img bs=1M count=10240
    losetup /dev/loop0 /var/lib/disk.img
    
    echo<<_EOF_ >> /etc/rc.local
    losetup /dev/loop0 /var/lib/disk.img
    _EOF_


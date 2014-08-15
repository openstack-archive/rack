Ansible playbook for OpenStack Log collection and analysis
=================

# Description
Since OpenStack logs are dispersed across the nodes and components, it is sometimes difficult to troubleshoot the error or simply grasp what is going on in OpenStack.
Using fluentd(td-agent), elasticsearch and Kibana, you can easily locate the error and quickly grasp the status from logs.
As basic UUIDs (userID, tenantID, instanceID, requestID, etc.) are indexed, you can quickly search and corner the cause of error with them, too.


This repository contains playbooks to setup fluentd(td-agent) and elasticsearch.
Fluentd collects logs from all OpenStack nodes and you can analyze them with elasticsaerch/Kibana.


These playbooks do..
* install Elasticsearch to elasticsearch node.
* install td-agent to collector node.
* install td-agent to all OpenStack nodes
* provide Kibana dashboard with cool UI.


# Requirements
* Ansible 1.6 or later
* CentOS 6.5 or later
* Internet accessible network
* OpenStack (tested on Icehouse)

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
	
### Role of each nodes
Determine the role of each nodes in log_hosts file  
 * [elasticsearch]: elasticsearch+Kibana node
 * [fluentd_collector]: Collector node
 * [openstack]: All OpenStack nodes


### elasticsearch/fluentd/Kibana settings
Edit the group_vars/all file to accomodate with you environment.


### Interface mapping
Determine interface mapping of External/Internal/Management for each role nodes.
Edit `group_vars/{everything except all}` and specify which interface to use for which network.
In default, eth1 for Internal, eth2 for External and eth3 for Management.


# How to run
Go to the top directory (where log_hosts and set_log.yml are located), and `ansible-playbook set_log.yml`
Or you can use Jenkins to kick playbook with following shell script.

    /usr/bin/ansible-playbook $WORKSPACE/set_log.yml


# Load Kibana dashboard
Access elasticsearch/Kibana node with browser. If you are lucky, you can see kibana dashboard.

Go to _Load_-> _Advanced_-> _LocalFile_, and select `OpenStackLogDashboard` you downloaded with playbooks.


***
# Tips
## faster installation
You can pick up your own repositories to install faster.
Place your repository files in `templates/etc/yum.repos.d` directory and set `use_your_own_repository true` in `group_vars/all`.


***
## TODO
 * Input ceilometer data to analyze
 * Use fluent-plugin-multi-format-parser for much understandable regexp definitions.
 * Cluster the Elasticsearch


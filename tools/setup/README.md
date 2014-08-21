# How to work RACK

## Overview

This text explains how to create "Rack" Image.  
"Rack" image is the source of both "API" VM and "Proxy" VM.  

## Workflow

### 1. Install RPM based Linux Operation System

* setup RPM based Linux like Fedora/CentOS in your OpenStack environment to create "Rack" image.  
  (In advance, we did this workflow at CentOS 6.5. We recommend to use same OS version to avoid any problems.)  
* you need to install Git for cloning "Rack" image building tool and connect to the internet.  

### 2. Clone "Rack" In Your VM From Github

```
    [SSH:]   git clone?git@github.com:stackforge/rack.git
    [HTTPS:] git clone?https://github.com/stackforge/rack.git
```

### 3. Execute "Rack" Image Build Tool(imagebuid.sh)  

* __System commands run in this process.__  
  __You should consider any other application compatibility before running.__  

```
    /your/rack/path/tools/setup/imagebuild.sh  
```
 
### 4. Shutdown VM and Create Snapshot of VM image

* Use nova client or horizon to shutdown VM and create a snapshot of it.  
  And note your "Rack" grance image id.  

### 5. Start "API" role VM

* Execute command below.  

```
    nova boot \  
    --image ${RACK_GRANCE_IMAGE_ID} \  
    --flavor ${FLAVLOR_ID_THAT_HAS_AT_LEAST_2GB_MEMORY} \  
    --nic net-id=${YOUR_NETWORK_ID} \  
    --meta "roles=api/mysql/rabbitmq/scheduler/resourceoperator" \  
    --meta "sql_connection=mysql://root:password@127.0.0.1/rack?charset=utf8" \  
    --meta "os_username=${OPENSTACK_USER_NAME}" \  
    --meta "os_password=${OPENSTACK_PASSWORD}" \  
    --meta "os_tenant_name=${OPENSTACK_TENANT_NAME}" \  
    --meta "os_auth_url=${OPENSTACK_AUTH_URL}" \  
    --meta "rabbit_password=guest" \  
    --meta "rabbit_host=localhost" \  
    --meta "rabbit_userid=guest" \  
    rack-api
```

* Add inbound SecurityGroupRule below 

```
    8088:TCP API
    3306:TCP mysql
    5672:TCP rabbitmq
```

### 6. Test API

* As soon as you start "API" role VM, rack api process run automatically.  

* Login to VM and Use RackClientTool to test API.  
  If you succeed, you renspond group data in json body. 

```
    export OS_USERNAME="demo_user"
    export OS_TENANT_NAME="demo_user"
    rack_client group-create --name=test
```

### 7. Experience Rack Application
[pi-montecarlo] (https://github.com/stackforge/rack/tree/master/tools/sample-apps/pi-montecarlo)
[tweet-analyzer] (https://github.com/stackforge/rack/tree/master/tools/sample-apps/tweet-analyzer)

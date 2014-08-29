# RACK Sample Program - PI calculation

##Overview
This application calculates the approximate value of PI using the "Monte Carlo method". The Monte Carlo is a method to calculate iteratively to gain an approximate result. The more you iterate the calculation, the more precise result will be.
You can specify the "number of trials" and "number of processes(instances)" in this application.
You will get more precise PI with "a larger number of trials", but it takes longer to get the result.
Then you can make it faster with larger "number of process", as more instance performs distributed processing.
Ultimately, you can obtain a more precise value of PI faster with RACK.

##Preparation Procedure
This chapter describes the preparation and setting up of RACK.
After completing this chapter, you will have one RACK API, one glance image and one RACK proxy.

### Deploy RACK API
RACK API is required to control RACK Proxy.
Please refer to [How to use RACK](https://github.com/stackforge/rack/tree/master/tools/setup) to deploy RACK API for detailed procedure.

###Create an Image
We provide `imagebuild.sh` to build an image from CentOS 6.x instance. We tested it on CentOS6.5.
First, launch an instance from CentOS6.5 image and log in to it as the root user and install git and rack.git.
Then execute `imagebuild.sh` to build the sample application's image.

```
# yum install -y git
# git clone https://github.com/stackforge/rack.git
# cd ./rack/tools/sample-apps/pi-montecarlo/
# ./imagebuild.sh
```

When it is finished, shutdown the instance and save a snapshot.

###Deploy RACK Proxy
Before deploying an application, you have to deploy RACK Proxy.
Please log in to RACK API and edit `group-init.conf`.
This is a configuration file for `rack-client`.
Fill in the blanks depending on your environment.

####./rack/tools/group-init.conf.
```
[group]
name = {Group name}     ### ex: pi_test
[network]
cidr = {Network address in CIDR format}     ### ex: 10.0.2.0/24
ext_router_id = {Your rooter ID}
[securitygroup]
securitygrouprules = 
    protocol=tcp,port_range_max=80,port_range_min=80,remote_ip_prefix=0.0.0.0/0
    protocol=tcp,port_range_max=5000,port_range_min=5000,remote_ip_prefix=0.0.0.0/0
    protocol=tcp,port_range_max=8088,port_range_min=8088,remote_ip_prefix=0.0.0.0/0
    protocol=tcp,port_range_max=8888,port_range_min=8888,remote_ip_prefix=0.0.0.0/0
[proxy]
nova_flavor_id = {Any Flavor ID you like(We recommend a flavor with at least 2GB memory)}
glance_image_id = {Your proxy image ID}
```

Then execute the following command.
This command creates a new keypair, a new security group, a new network, assigns group id(`gid`) and process id(`pid`).

```
# export OS_USERNAME=demo_user
# export OS_TENANT_NAME=demo_tenant
# rack_client group-init --config-file /path/to/group-init.conf
gid: 8612d17d-737e-4050-be93-cd49b1574e1e
keypair_id: da6bde2d-1753-410a-9f2a-3a99c88584f6
securitygroup_id: 1cd37c45-f38e-4407-9bd6-cb2222ad928d
network: 8c627394-e4cd-4c9e-972c-fad704323966
pid: f08d3e1b-5b51-4fd6-849a-5b7983f35c0d
```

Note that variables, `OS_USERNAME` and `OS_TENANT_NAME` will be registered on RACK database as someone who executed the command.
It's not related to OpenStack username and tenant name.
Note values above and bring it to the following commands as option.
Now you can see a further instance launched on your OpenStack environment.
Ensure the RACK Proxy is deployed successfully by running the following command.

```
# rack_client --url http://{proxy's IP address}:8088/v1/ proxy-show --gid {gid}
{"proxy": {"status": "ACTIVE", "userdata": null, "ppid": null, "user_id": "demo_user","name": "pro-f08d3e1b-5b51-4fd6-849a-5b7983f35c0d", "ipc_endpoint": {"host": "10.0.50.2", "port": "8888"}, "app_status": "ACTIVE", "pid": "f08d3e1b-5b51-4fd6-849a-5b7983f35c0d", "args": {"roles": "ipc/shm/api/proxy"}, "fs_endpoint": null, "gid": "8612d17d-737e-4050-be93-cd49b1574e1e", "keypair_id": "da6bde2d-1753-410a-9f2a-3a99c88584f6", "nova_flavor_id": 3, "shm_endpoint":{"host": "10.0.50.2", "port": "6379"}, "project_id": "demo_user", "glance_image_id": "1725f6c0-264a-4202-8886-7998dfe4457b"}}
```

It's okay if you get a JSON response like above.

###Register Swift endpoint
As the sample application stores result on `File System`, you need to register keystone credentials on RACK Proxy so that RACK Proxy can store the result on Object Storage(Swift).
Please register your credentials on RACK Proxy by executing the following commands.

```
# export OS_USERNAME={openstack username}
# export OS_PASSWORD={openstack password}
# export OS_TENANT_NAME={openstack tenant name}
# export OS_AUTH_URL={openstack keystone endpoint}
# rack_client --url http://{proxy's IP address}:8088/v1/ proxy-update --gid {gid} \
  --fs_endpoint {\"host\":\"$OS_AUTH_URL\"\,\"name\":\"picalc_result\"} --app_status ACTIVE
```

And you also need to create a Swift container with the name of `gid` value, in this example "8612d17d-737e-4050-be93-cd49b1574e1e".

##Run Sample Program
Execute the following command to run the program.

```
# OS_USERNAME={openstack username}
# OS_PASSWORD={openstack password}
# OS_TENANT_NAME={openstack tenant name}
# /path/to/rack/tools/sample-apps/pi-montecarlo/app/picalc.sh {SampleProgramImageID} {number of trials} {number of process}
```

When the process is complete, you will have `result.txt` at the swift container.

####result.txt
```
------------------------------------------------------------------`
picalc result
------------------------------------------------------------------`
 trials        : 10000000
 process       : 10
 within circle : 7855266
------------------------------------------------------------------`
 pi            : 3.14159265359
 result        : 3.1421064
 error         : 0.000513746410207
------------------------------------------------------------------`
 time          : 00 d 00 h 00 m 26 s
------------------------------------------------------------------`
```

Please check the `error` and `time` vary as you change the `{number of trials}` and `{number of process}`.

# PI Calculation Rack Sample Program
##1. Getting Start
This sample program, parallel distributed processing the approximate value of pi calculated by Monte Carlo method using the RACK-API.  
The program has two parameters as "number of trials" and "number of processes".
The number of trials, it is processing by dividing specified in the Number of processes, and outputs to the "Swift Storage" by summing the results of each process.

##2. Setup Example
The following is a setup scenario for PI Caluculation Program.

* Create Image  
 
 Sample program execution image that you create using your "CentOS-6.5" boot image.
* Proxy Create  
  
  Proxy process, relaying of inter-process communication and hold the endpoint information.
* Proxy Update  
  
  "Proxy Update", registers the container name and Swift endpoint.

 ###2-1. Create Image 
 * In OpenStack Dashboard, please launch an instance from your "CentOS-6.5" boot image.  
 * Please copy the following file into the user's home directory of launched instance.  
```
./rack/tools/sample-apps/pi-montecarlo/imagebuild.sh
```

 * From the shell of the launched instance, please run the imagebuild.sh that you copied. 
Will build the environment required to run.
```
$ sh ./imagebuild.sh
```
In OpenStack Dashboard, please create a snapshot of this instance.
Image ID is specified in the argument of the sample program. 
(Section 3)  

 ###2-2. Proxy Create
 * Please edit the required parameters of the group-init.conf file. 
 
   ./rack/tools/group-init.conf.  
```
[group]  
name = <AnyValue>     ### ex: pi_test
[network]
cidr = <AnyValue>     ### ex: 10.0.2.0/24  
ext_router_id = <YourRooterId>
[securitygroup]
securitygrouprules = protocol=tcp,port_range_max=80,port_range_min=80,remote_ip_prefix=0.0.0.0/0 protocol =tcp,port_range_max=5000,port_range_min=5000,remote_ip_prefix=0.0.0.0/0  protocol=tcp,port_range_max=8088,port_range_min=8088,remote_ip_prefix=0.0.0.0/0  protocol=tcp,port_range_max=8888,port_range_min=8888,remote_ip_prefix=0.0.0.0/0
[proxy]
nova_flavor_id = 3  
glance_image_id = <YourProxyImageId>```
The proxy image, you need to create in advance by the "Rack" Image Build Tool (imagebuid.sh) .
 * Please execute the following command.  
```
$ export OS_USERNAME=<UserName>
$ export OS_TENANT_NAME=<YourTenantName>  
$ cd ./rack/tools  
$ python rack_client.py --url http://<ProxyFloatingIP>:8088/v1/ group-init --config-file group-init.conf
```

 * When you run a group-init command, The following dumps are output.
Please paste the --gid option of proxy-update command in the section 2-3.  
```
gid=b60bdb69-1751-4b88-b129-d41f044c858  
keypaire_id=f19db0a3-6ab3-4a88-ad72-f90d5aa9e0f4  
securitygroup_id=12aac225-662f-4a06-82c9-ad06b546b9a8  
                        ：
```

 ###2-3. Proxy Update
 * Please execute the following command. 
```
$ cd ./rack/tools  
$ python rack_client.py proxy-update --url http://<ProxyFloatingIP>:8088/v1/ --gid <gid> --fs_endpoint {\"host\":\"<YourSwiftStrageHost>\",\"name\":\"<YourContainerName>\"}`  
```
`ex. --fs_endpoint {\"host\": \"http://192.168.100.19:5000/v2.0\",\"name\": \"picalc_result\"}`  

   Update is successful. The information of the proxy will be response in JSON format.

##3. Running Sample Program  
* Please copy the following file into the user's home directory of proxy instance.  
```
./rack/tools/sample-apps/pi-montecarlo/app/picalc.sh
```  

* From the shell of the proxy instance, please execute the following command.  
```
$ export OS_USERNAME=<UserName>
$ export OS_PASSWORD=<Password>
$ export OS_TENANT_NAME=<YourTenantName>
$ ./picalc.sh <SampleProgramImageID> 10000000 10  
```
 Usage : picalc.sh IMAGE_ID NUMBER_OF_TRIALS NUMBER_OF_PROCESS   
 
 When the process is complete, result.txt file will be output to your container.
Please see the result.txt file.  
  

+ Results such as the following will be output.  
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
# The concept of RACK: "OpenStack Native Application"

OpenStack Native Application is the software, which uses OpenStack resource (eg. VM or VNET) directly from application. Recent popular applications are designed before the cloud computing age, so affinity with cloud is not considered. In order to make those applications work on OpenStack, tools such as Chef, Puppet and other tools are required, and it makes systems very complex in design.

RACK provides the mechanism to create “After the Cloud” applications. Programmer can write codes that are scalable and migratable on OpenStack platform without cooperating with the external systems.

Concepts of RACK are as follows:

1. RACK handles VM with "functions" as a single execution binary file. “Functions” here means OS, middleware and programs that are necessary for application to function. The programs here are made in such a way as to call and operate RACK API.
2. When this execution binary is deployed onto OpenStack, the VM will behave like a Linux process and then finish its own task.
3. This process is based on the descriptions in the program. It does things such as forking and generating a child process, communicating between processes.

Please take a look at our Wiki page to understand RACK more!
**https://wiki.openstack.org/wiki/RACK**

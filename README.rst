RACK(Real Application Centric Kernel) README
=====================

RACK provides the ability that can control OpenStack as program resource with an application.
From an application, the VM instance looks like the Linux process through the RACK, so you can use "Exec", "Fork", "Kill" commands against the processes(actually VMs).
It enables you to implement a large scale distributed system in a variety of programming languages on OpenStack.

You can use RACK in many cases.
Followings are some examples.

* You can implement a new architecture application.
  For example, you can build an application that calculates the necessary amount of computing resource(i.e. instance) depending on the data to process and launches additional instances dynamically.
  Then, the data will be processed very quickly since these instances work in parallel.
  This new architecture application is suitable for processing a large amount of data.

* You can integrate existing system such as batch system with Hadoop and Web application using RACK.
  For example, RACK enables you to deploy Hadoop cluster easily and add autoscale function to your Web applications. 

To learn about RACK in detail, read this page on the wiki:

  https://wiki.openstack.org/wiki/RACK


# The application to approximate the circular constant with the Monte Carlo method

This chapter describes an application to approximate the Pi (circular constant) with Monte Carlo method as an example to the distributed application utilizing RACK.


# Calculate the approximate circular constant with the Monte Carlo method

The Monte Carlo method approximates using repeated random sampling.You can refer to the other web sites for details of approximation of Pi, but in a nutshell, this method approximates with following equation. 

```
π = 4 × (1/4 of area of circle) / (area of regular tetragon)
```
Here, generate random numbers x and y, and plot them inside regular tetragon P(x, y) repeatedly. 
Then the ratio between the number of points "inside 1/4 of circle" and that of points "inside regular tetragon" approaches the ratio between "1/4 of area of circle" and "area of regular tetragon". This ratio is an approximation of Pi.

Ultimately, you can approximate  Pi with the following equation.

```
π = 4 × (# of points inside 1/4 circle) / (# of points inside regular tetragon)
```


## Breaking limitation with RACK

With more repeated samples, Monte Carlo method approximates more precise value and it takes longer time.
It is an inevitable limitation you encounter with the limited computation resources.

Here we will implement RACK to break this limitation.

Feeding number of repetition and number of nodes for calculation as parameters, this system scale out itself according to the parameters and calculates at high speed.


## Application Flow

This application consists of a parent process and child processes.
Parent process forks a child process in accordance with fed parameters and Child processes are used for calculation.

First, parent process calculates the `number of calculation for each child(trials_per_child)` from two parameters `number of repetition(trials)` and `number of nodes(workers)`.

Secondly, parent process forks a child process as much as `workers`.
Then parent process waits for completion of calculation by child processes.

The each child process has the parameter `trials_per_child`. They start calculation after boot, and after `trials_per_child` times, reports the result to parent process. Here, child process reports via `pipe` which `rack-proxy` provides.

At last, parent process tallies results from child processes and calculates ultimate approximation.
Those calculation results are stored at `file_system` which `rack-proxy` provides.


![montecarlo-1](montecarlo-1.png "montecarlo-1")
![montecarlo-2](montecarlo-2.png "montecarlo-2")


## Preparing application

### 1. Create a Glance image(snapshot)

Both parent process and child process share the same Glance image.
It changes its role by checking the existence of parent process at boot.

First, boot the VM from Horizon or Nova CLI. Please use `CentOS-6.5` based Glance image, and make sure VM  can connect to the Internet.

Secondly after boot, login as root and execute following commands. This `imagebuild.sh` installs required packages and configure them.

```
# git clone https://github.com/stackforge/rack
# cd rack/tools/sample-apps/pi-montecarlo
# ./imagebuild.sh
Start image building...
...

****************************************
Finish image building.
Shutdown and save snapshot of this instance via Horizon or glance command.
****************************************
```

Above message indicates installation and configuration complete. Shutdown VM and **create a snapshot** from Horizon or Glance CLI.

Following message indicates installation and configuration finished properly. Please resolve issue and run `imagebuild.sh` again.

```
****************************************
Error occurred. Execution aborted.
Error: Installing the required packages
****************************************
```


### 2. Initialize the process group

This section describes how to set up an environment for this application. `rack-api` needs to be run before proceeding this step.
For details of installation of `rack-api`, please refer to [**here**](https://github.com/stackforge/rack/tree/master/tools/setup).

First, we will create a configuration file for process group initialization on RACK CLI installed machine.
For details of installation of RACK CLI, please refer to [**here**](https://github.com/stackforge/python-rackclient).

Please fill empty section with your environment parameters.

**group.conf**
```
[group]
name =

[keypair]
is_default = True

[network]
cidr =
ext_router_id =
dns_nameservers =

[securitygroup]
rules =
    protocol=tcp,port_range_max=8088,port_range_min=8088,remote_ip_prefix=0.0.0.0/0
    protocol=tcp,port_range_max=8888,port_range_min=8888,remote_ip_prefix=0.0.0.0/0
    protocol=tcp,port_range_max=8080,port_range_min=8080,remote_ip_prefix=0.0.0.0/0
    protocol=tcp,port_range_max=6379,port_range_min=6379,remote_ip_prefix=0.0.0.0/0

is_default = True

[proxy]
nova_flavor_id =
glance_image_id =
```

Run following commands to initialize the process group.

```
$ export RACK_URL=http://{ IP address of rack-apiVM }:8088/v1
$ rack group-init group.conf
...
+------------------+--------------------------------------+
| Property         | Value                                |
+------------------+--------------------------------------+
| gid              | d5e7711b-38fb-4ae3-a3c5-3d4b88a3983d |
| keypair_id       | 4ae497df-4f41-4cc3-bb11-14f7d8fff0ef |
| network_id       | f1cff914-c9e8-4a8e-ba51-4f0481680c89 |
| proxy pid        | 8377f985-6b68-4eb5-a0c0-502cc06a4edd |
| securitygroup_id | 2e965967-2f43-4a1b-9aa2-1e9e321ecbd7 |
+------------------+--------------------------------------+
```

You will see `rack-proxy` VM boots. Please check `rack-proxy` works properly by running the following commands.

```
$ rack --rack-url http://{IP address of rack-proxyVM}:8088/v1 group-list
+--------------------------------------+---------+-------------+--------+
| gid                                  | name    | description | status |
+--------------------------------------+---------+-------------+--------+
| d5e7711b-38fb-4ae3-a3c5-3d4b88a3983d | test    | None        | ACTIVE |
+--------------------------------------+---------+-------------+--------+
```

This completes initialization of a process group.


### 3. Run the application

Running application is pretty straightforward, just define the parameters and boot the Glance image created at step#1.

RACK CLI can pass arbitrary parameters to the application via `--args` option. In this example, we are passing three parameters `trials`, `workers` and `stdout`.
`trials` and `workers` parameters are described at chapter Application Flow.

We are specifying result save path at paramter `stdout`, with slash separated path like filesystem. In this example, we are using `/output/result.txt` as save path.

Now, run the following commands to execute the application. Fill the enviroment variable `RACK_GID` with created process group `gid`.

```
$ export RACK_GID=d5e7711b-38fb-4ae3-a3c5-3d4b88a3983d
$ rack process-create ¥
  --nova_flavor_id {flavor id} ¥
  --glance_image_id {Glance image ID created at step #1} ¥
  --args trials=1000000,workers=3,stdout=/output/result.txt
```

When calculation ends properly, all processes are removed automatically. 
You can get the calculation results with following command from `filesystem`.

```
$ rack file-get --proxy_ip {IP address of rack-proxyVM} /output/result.txt
$ cat result.txt
+----------+-------------------+
| Property | Value             |
+----------+-------------------+
| trials   | 1000000           |
| workers  | 3                 |
| points   | 785444            |
| pi       | 3.14159265359     |
| result   | 3.141776          |
| error    | 0.00018334641     |
| time     | 63.4065971375     |
+----------+-------------------+
```

### 4. Check the application performance

The result of this application varies depending on parameters you set.
Larger `trials` and `workers` will result with more precise Pi while maintaining the necessary time to calculate.
On the other hand, larger `workers` and fixed `trials` will end up with shorter time to calculate.


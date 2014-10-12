EzBake in a Box
===============

What is it?
-----------

This project contains tools that are required to get a developer up and running
locally with EzBake. These tools provide a mechanism to start thrift services
and Frack pipelines. You can choose to run these services locally if you are
already developing in a Linux environment, or use the Vagrant VM.

Requirements
------------

 - Git client to clone this repository
 - Vagrant (http://docs.vagrantup.com/v2/installation/index.html)
 - Virtual Box (https://www.virtualbox.org/)
 - Maven
 - Python (for now)

What Now?
---------

Clone this repository to get everything you need.

### Create Your Buildpack File (This is not currently a real buildpack).

This project contains a sample sample.buildpack which includes starting up the
Data Warehouse Service and a Frack Pipeline. You will need to create your own
buildpack. Include your application name, what auths your application requires,
what thrift services your application depends on, and any Frack pipelines you
would like to have running.

### Get Your Dependencies

The easiest thing to do is to add your frack pipelines and thrift services as
dependencies to the pom.xml in this project. And then run: `mvn package`.
Remember, your frack pipelines and thrift services must be
`jar-with-dependencies`.

### Build

Create your buildpack file.

Sample Buildpack:

	{
		"appName": "sampleapp",
		"auths": ["U", "S", "TS"],
		"services": [
			{
				"runner": "java",
				"options": "-j warehaus.jar -s warehaus -x warehaus"
			},
			{
				"runner": "java",
				"options": "-j quarantine.jar -s quarantine -x quarantine -c ezbake.quarantine.service.QuarantineService"
			}
		],
		"pipelines": [
            {
                "jar": "path/to/pipeline.jar",
                "id": "pipeline1"
            },
            {
                 "jar": "path/to/some/other/pipeline.jar",
                 "id": "pipeline2"
             }
        ]
	}


Generate your Vagrantfile and startup script:

	./buildVagrant.py <buildpack filename>

This will generate a Vagrantfile and a bootstrap.sh.

#### Security ID
All datasets/services are required to have `-D ezbake.security.app.id=<APP_SECURITY_ID_HERE>` as well as `-x <APP_SECURITY_ID_HERE>`. All services/datasets that are part of the same top level application should share a security id. The security id must match one of the security ids listed in FileBackedRegistrations.json. 

#### Application ID
Another important attribute for datasets and servicesis `-D application.name=<APP_NAME>` and `-a <APP_NAME>`. Without a valid application name most services and datasets will fail to start. For common services ie the datawarehaus an application name of `common_services` should be used.

### Configuration Directories

All site configuration parameters (accumulo host/port, redis host/port, etc) are
stored in the conf directory. This configuration information will be provided
in the production environment at some central location. All user configuration
properties files (for pipelines) should be added into the user-conf directory.
A sub directory for each running pipeline should be created, and include that
pipeline's properties files. For example, if you are running a pipeline called
'test-pipeline', place all of its properties files under user-conf/test-pipeline.
These files will be loaded and merged into the EZConfiguration object once
the pipeline is submitted. It is not necessary to store the user properties
files in the pipeline jar that is being submitted. Examples of user properties
are application.name, ezbake.security.app.id, and any other application specific
properties that you need in your pipeline.

### Debugging Pipelines

In order to debug a pipeline, update the frack-submitter.json file with the
following information:

`"command" : java -Dezbake.frack.submitter.log=##LOG_FILE## -Dlog4j.configuration=ezbake-dev-tools-log4j.properties
 -cp ./frack:ezbroadcast-redismq.jar:frack-submitter.jar:##JAR_FILE## ##MAIN_CLASS## 
 -s ##SUBMITTER_CLASS## -b ##BUILDER_CLASS## -i ##PIPELINE_ID## ##ARGUMENTS##"

should become

`"command" : java -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=13000
 -Dezbake.frack.submitter.log=##LOG_FILE## -Dlog4j.configuration=ezbake-dev-tools-log4j.properties 
 -cp ./frack:ezbroadcast-redismq.jar:frack-submitter.jar:##JAR_FILE## ##MAIN_CLASS## 
 -s ##SUBMITTER_CLASS## -b ##BUILDER_CLASS## -i ##PIPELINE_ID## ##ARGUMENTS##"

Where "address=13000" should contain a port number that is not in use. You can
then connect a remote debugging tool to that port and trace through your
pipeline code.

The logging level for pipelines can also be updated in the frack/ezbake-dev-tools-log4j.properties
file. This may be helpful in viewing other logging level information from your pipelines.

### Security

If your pipeline is broadcasting ANY information, or you are using an application
that sends requests to services, this section applies to you.

By default, the security service will be running locally in file-backed mode.
The files that need to be updated in order to properly utilize the security
service are FileBackedRegistrations.json and MockUserService.json.

If you do not yet have a set of certificates and a truststore,
register with the security service. In the mean time you can use the provided
sample client certs (in the ssl/client directory) and public key in the file.
After obtaining certs and a keystore from the security service, please update
your local instance to use that information.

By default, the security service client (EzbakeSecurityClient) will look in
the `ssl/<your-app-id>` directory for certificates. So, if you are attempting
to initialize a security client add a folder with your app ID under the ssl
directory and put your certs (or the provided sample client certs) under that
directory. FileBackedRegistrations.json contains application/pipeline authorization info.
To obtain auth info from the file backed service, add an entry in that file for
your application, using the same ID that was used as the folder name above.

MockUserService.json contains user information which is used to sign requests
between services. If you require signatures, you must add an entry for the user
which you are going to be using to send requests. Users are looked up by DN,
which is the combination of CN, O, OU, and C. For example
"CN=Bob Smith, OU=Ezbake, O=Ezbake, C=US".

In production each application/pipeline will need to register with the security
service, and will be provided with it's application ID in order to get its
authorizations. If your application is already registered with the security
service, please use the same ID locally as to avoid dual maintenance.

The application/pipeline will also need to set a configuration parameter (in
EZConfiguration) which signifies its security service provided application ID.
The configuration parameter is 'ezbake.security.app.id'.

### Run

If you are running in a Linux environment, you can just run:

	./bootstrap.sh local

This will start a local zookeeper instance (running on port 2181), a local
Accumulo cluster (dynamic port), and all the services and pipelines you
specified in your build file. When you are done, run: `./killProcess.sh` to
kill the process the bootstrap file created.

If you want to run these services in Vagrant:

	vagrant box add ezbake https://www.ezbake.io/resources/ezbake.box --insecure
	vagrant up

The Vagrant VM is running Zookeeper, Accumulo, Kafka, ElasticSearch, and Redis.
By default, Zookeeper and the services are all configured with port forwarding
in the VM. So zookeeper is available at localhost:2181, even though it is now
running in the VM. If you are currently using EzDiscovery, you should not need
to know the ports for your thrift services because the Thrift Runner has
registered those ports for you. The VagrantFile contains a line to turn the VM
into Bridged mode, which would make these services available to other VMs or
other computers on the network. Feel free to modify the Vagrantfile and
`bootstrap.sh` to better meet your individual needs.



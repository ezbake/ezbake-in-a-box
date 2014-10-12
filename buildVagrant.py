#!/usr/bin/env python
"""Generates a Vagrantfile and bootstrap.sh for use with VirtualBox.

Takes the path to a buildpack file in order to setup the correct port
forwarding and bootstrap commands.
"""

import os
import json
import time
import sys

#main
if __name__ == "__main__":
    jsonFile = open(sys.argv[1])
    jsonConfig = json.load(jsonFile)
    jsonFile.close()
    #Write out Vagrant File
    staticIp = "192.168.50.101"
    v = open('Vagrantfile', 'w')
    v.write('VAGRANTFILE_API_VERSION = "2"\n')
    v.write('Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|\n')
    v.write('config.vm.box = "ezbake"\n')
    v.write('config.vm.provision "shell", path: "bootstrap.sh", args: "VAGRANT"\n')
    v.write('config.vm.hostname = "EzbakeVagrant"\n')
    v.write('config.vm.network "private_network", ip: "{0}"\n'.format(staticIp))

    s = open('bootstrap.sh', 'w')   
    s.write('#! /bin/bash\n\n')

    #s.write('/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties &\n\n')
    # Disable iptables until it is fixed in the VM
    s.write('if  [ "$1" != "local" ] && [ "$1" != "VAGRANT" ] ; then\n')
    s.write('   echo "Need an argument. \'local\' or \'VAGRANT\'" >&2\n')
    s.write('   exit\n');
    s.write('fi\n')

    s.write('service iptables stop && chkconfig iptables off\n')
    s.write('if [ $1 == "VAGRANT" ]\n')
    s.write('then\n')
    s.write('   service zookeeper restart\n')
    s.write('   cd /vagrant/\n')
    s.write('   # Elasticsearch plugin configuration\n')
    s.write('   cp elasticsearch.yml /etc/elasticsearch/\n')
    s.write('   cp elastic-security-* /usr/share/elasticsearch/lib/elastic-security.jar\n')
    s.write('   sh -c "service elasticsearch restart"\n')
    s.write('else\n')
    s.write('   sh -c "java -jar local-zookeeper-jar-with-dependencies.jar 2181 &"\' echo $! > zoo.pid\' &\n')
    s.write('   sleep 5\n')
    s.write('fi\n')
    s.write('export PRIVATE_KEY_LOCATION=test_key.priv\n')
    s.write('export PUBLIC_KEY_LOCATION=test_key.pub\n')
    s.write('export EZCONFIGURATION_DIR=conf\n')


    auths = ' '.join(["{0}".format(x) for x in jsonConfig['auths']])
    s.write('sh -c "java -Xmx512m -jar local-accumulo-jar-with-dependencies.jar {0} &"\' echo $! > acc.pid\' &\n'.format(auths))
    s.write('sleep 5\n')
    s.write('ACC_ZOO_PORT=\'12181\'\n')
    s.write('if [ ! -d "conf" ]\n')
    s.write('then\n')
    s.write('    mkdir conf\n')
    s.write('fi\n')
    s.write('sed -e s/##ACCUMULO_ZOO_PORT##/$ACC_ZOO_PORT/g ezbake-config.template > conf/ezbake-config.properties\n')

    ezsecurityport=12996

    # Provision databases when running in vagrant and do it before we try to start up services that depend on them
    if 'databases' in jsonConfig:
        s.write('if [ $1 == "VAGRANT" ]\n')
        s.write('then\n')
        for db in jsonConfig["databases"]:
            if db["name"] == 'mongodb':
                s.write('   if !(ls /etc/init.d/ | grep mongo >/dev/null); then\n')
                s.write('       echo "Installing MongoDB 2.5.4 and dependencies..."\n')
                s.write('       yum -y install dos2unix openssl net-snmp net-snmp-libs net-snmp-utils cyrus-sasl cyrus-sasl-lib cyrus-sasl-devel cyrus-sasl-gssapi\n')
                s.write('       mkdir -p /usr/share/mongodb\n')
                s.write('       mkdir -p /var/lib/mongodb\n')
                s.write('       cd /usr/share/mongodb/\n')
                s.write('       curl -O http://downloads.10gen.com/linux/mongodb-linux-x86_64-subscription-rhel62-2.5.4.tgz\n')
                s.write('       tar -zxvf mongodb-linux-x86_64-subscription-rhel62-2.5.4.tgz\n')
                s.write('       ln -s mongodb-linux-x86_64-subscription-rhel62-2.5.4/ current\n')
                s.write('       cp /vagrant/mongo-files/mongod /etc/init.d/\n')
                s.write('       #dos2unix /etc/init.d/mongod\n')
                s.write('       chmod u+x /etc/init.d/mongod\n')
                s.write('       service mongod start\n')
                s.write('       chkconfig --add mongod\n')
                s.write('       chkconfig --list | grep mongod\n')
                s.write('       chkconfig mongod on\n')
                s.write('       echo "MongoDb installed, listening on 27017."\n')
                v.write('       config.vm.network :forwarded_port, host: 27017, guest: 27017\n')
                s.write('   fi\n')
            if db["name"] == 'postgresql':
                s.write('   if !(rpm -qa | grep postgres >/dev/null); then\n')
                s.write('       echo "Installing PostgreSQL 9.3 and dependencies..."\n')
                s.write('       curl -O http://yum.postgresql.org/9.3/redhat/rhel-6-x86_64/pgdg-centos93-9.3-1.noarch.rpm\n')
                s.write('       rpm -ivh pgdg-centos93-9.3-1.noarch.rpm\n')
                s.write('       yum -y install postgresql93-server\n')
                s.write('       service postgresql-9.3 initdb\n')
                s.write('       chkconfig postgresql-9.3 on\n')
                s.write('       echo \"listen_addresses = \'*\'\" | sudo tee -a /var/lib/pgsql/9.3/data/postgresql.conf\n')
                s.write('       echo \"host all all  0.0.0.0/0 md5\" | sudo tee -a /var/lib/pgsql/9.3/data/pg_hba.conf\n')
                s.write('       service postgresql-9.3 stop\n')
                s.write('       service postgresql-9.3 start\n')
                s.write('       su - postgres -c "psql -U postgres -d postgres -c \\"alter user postgres with password \'secret\';\\""\n')
                s.write('       echo "PostgreSQL 9.3 installed, listening on 5432."\n')
                v.write('       config.vm.network :forwarded_port, host: 5432, guest: 5432\n')
                s.write('   fi\n')
        s.write('   cd /vagrant/\n')            
        s.write('fi\n')

    # Vagrant services startup
    port = 13002
    s.write('if [ $1 == "VAGRANT" ]\n')
    s.write('then\n')

    s.write('   sh -c "java -jar ezbake-thrift-runner.jar -j ezbake-security-service-thrift-runnable.jar -c ezbake.security.service.processor.EzSecurityHandler -s EzBakeSecurityService -D ezbake.security.app.id=server -p {0} -h "{1}" > ezsecurity.log &"\' echo $! > ezbake-security-service.jar.pid\' &\n'.format(ezsecurityport, staticIp))
    for service in jsonConfig["services"]:
        sString = '   sh -c "java -jar ezbake-thrift-runner.jar {0} -p {1} -h {2} &"\' echo $! > {1}.pid\' &\n'.format(service["options"], port, staticIp)
        s.write(sString)
        s.write('   sleep 15\n')
        port += 1

    # Local services startup
    port = 13002
    s.write('else\n')
    s.write('   sh -c "java -jar ezbake-thrift-runner.jar -j ezbake-security-service-thrift-runnable.jar -c ezbake.security.service.processor.EzSecurityHandler -s EzBakeSecurityService -D ezbake.security.app.id=server -p {0} > ezsecurity.log &"\' echo $! > ezbake-security-service.jar.pid\' &\n'.format(ezsecurityport))
    for service in jsonConfig["services"]:
        sString = '   sh -c "java -jar ezbake-thrift-runner.jar {0} -p {1} &"\' echo $! > {1}.pid\' &\n'.format(service["options"], port)
        s.write(sString)
        s.write('   sleep 15\n')
        port += 1
    s.write('fi\n')
    # End Services startup

    if 'pipelines' in jsonConfig:
        for pipeline in jsonConfig["pipelines"]:
	    sString = 'sh -c "java -cp frack:ezbroadcast-redismq-jar-with-dependencies.jar:frack-submitter-service-jar-with-dependencies.jar:{0} -Dlog4j.configuration=ezbake-dev-tools-log4j.properties -Dezbake.frack.submitter.log={1}.log ezbake.frack.submitter.PipelineSubmitter -n -p {0} -i {1} &"\' echo $! > {0}.pid\' &\n'.format(pipeline["jar"], pipeline["id"])
            s.write('echo "Starting Pipeline {0}, follow log at {0}.log"\n'.format(pipeline["id"]))
            s.write(sString)
            s.write('sleep 10\n')

    v.write('config.vm.network :forwarded_port, host: 2181, guest: 2181\n')

    v.write('end')
    v.close()
    s.close()

    # Make sure the bootstrap.sh is executable.
    os.chmod('bootstrap.sh', 0o755)

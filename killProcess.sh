#! /bin/bash

for f in *.pid
do
	echo "Killing $f"
	kill -SIGTERM $(<$f)
	rm $f
done

echo "Killing local-accumulo zookeeper server main"
ps -ef | grep org.apache.zookeeper.server.ZooKeeperServerMain | grep -v grep | awk '{print $2}' | xargs kill -SIGTERM
echo "Killing local-accumulo Master"
ps -ef | grep org.apache.accumulo.server.master.Master | grep -v grep | awk '{print $2}' | xargs kill -SIGTERM

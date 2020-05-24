#!/bin/bash

SP2='  '
SP4='    '
SP6='      '
INTERVAL="2s"
PREFIX="global:\n${SP2}scrape_interval: $INTERVAL\n\nscrape_configs:"
TEMPLATE="${SP2}- job_name: {JOB}\n${SP4}scrape_interval: $INTERVAL\n${SP4}static_configs:\n${SP6}- targets: {TARGET}"
FILE_NO=$(ls -l ../hdac-node-descs | grep ^- | wc -l)

echo -e $PREFIX > prometheus-kubernetes-config.yaml

i=1
kubectl get pods -o wide | while read line
do
    if [[ "$line" == *"IP"* ]] || [[ $line == *"couchdb"* ]];then
        continue
    fi
    ip=$(echo $line | awk -F' ' '{print $6}')
    if [[ "$line" == *"hdac-seed"* ]];then
        echo -e "$TEMPLATE" | sed -e "s/{JOB}/\'hdac-seed\'/g" | sed -e "s/{TARGET}/[\'$ip:26660\']/g" >> prometheus-kubernetes-config.yaml
    else
        echo -e "$TEMPLATE" | sed -e "s/{JOB}/\'hdac-node$i\'/g" | sed -e "s/{TARGET}/[\'$ip:26660\']/g" >> prometheus-kubernetes-config.yaml
        i=$((i + 1))
    fi
done

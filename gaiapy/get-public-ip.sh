#!/bin/bash

TOTAL_NO=$(kubectl get nodes | wc -l)
TOTAL_NO=$((TOTAL_NO - 2))
GRAFANA=$((TOTAL_NO - 1))
PROMETHEUS=$((TOTAL_NO - 2))

rm /tmp/public-ips.txt
rm /tmp/nodes-info.txt

kubectl get nodes -o wide > /tmp/nodes-info.txt
i=0
while read line
do
    if [[ $line ==  *"NAME"* ]] || [[ $line == *"master"* ]];then
        continue
    fi
    prefix=""
    if [ $i -eq 0 ];then
        prefix="couchdb"
    elif [ $i -eq 1 ];then
        prefix="hdac-seed"
    elif [ $i -eq $PROMETHEUS ];then
        prefix="prometheus"
    elif [ $i -eq $GRAFANA ]; then
        prefix="grafana"
    else
        prefix="hdac-node"
    fi
      
    public_ip=$(echo $line | awk -F' ' '{print $7}')
    echo $prefix $public_ip >> /tmp/public-ips.txt
    i=$((i + 1))
done < /tmp/nodes-info.txt

if [ $# == 0 ];then
    echo "Please input (couchdb|hdac-seed|hdac-node|prometheus|grafana)"
    exit 0
fi

while read line
do
    if [[ $1 == "couchdb" ]];then
        if [[ $line == *"couchdb"* ]];then
            echo $line | awk -F' ' '{print $2}'
        fi
    elif [[ $1 == "hdac-seed" ]];then
        if [[ $line == *"hdac-seed"* ]];then
            echo $line | awk -F' ' '{print $2}'
        fi
    elif [[ $1 == "hdac-node" ]];then
        if [[ $line == *"hdac-node"* ]];then
            echo $line | awk -F' ' '{print $2}'
        fi
    elif [[ $1 == "prometheus" ]];then
        if [[ $line == *"prometheus"* ]];then
            echo $line | awk -F' ' '{print $2}'
        fi
    elif [[ $1 == "grafana" ]]; then
        if [[ $line == *"grafana"* ]];then
            echo $line | awk -F' ' '{print $2}'
        fi
    fi
done < /tmp/public-ips.txt

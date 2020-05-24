#!/bin/bash

if [ $# == 0 ];then
    echo "Please input param, friday or tendermint"
    exit 0
fi

if [ $1 != "friday" -a $1 != "tendermint" ];then
    echo "Please input param, friday or tendermint"
    exit 0
fi

TARGET=""
if [ $1 == "friday" ];then 
    TARGET="friday"
else
    TARGET="tendermint"
fi
    
FILE_NO=$(ls -l hdac-node-descs | grep ^- | wc -l)
FILE_NO=$(($FILE_NO -1))
TOTAL_NO=$(kubectl get nodes | wc -l)
#Grafana, Prometheus, CouchDB, HDAC SEED, Master Node and Title
HDAC_NODE_NO=$(($TOTAL_NO - 6))
READY_NO=$((TOTAL_NO - 3))
HDAC_NODE_NO_WITH_SEED=$(($TOTAL_NO - 5))

#waiting functions
waiting_single() {
    while true
    do
        res=$(kubectl get pods) 
        if [[ "${res}" == *"$1"*"Running"* ]];then
            break
        fi
    done
}

waiting_multi() {
    while true
    do
        kubectl get pods > /tmp/pods.txt
        cnt=0
        while read line
        do
            if [[ "${line}" == *"$1"*"Running"* ]];then
                cnt=$((cnt + 1))
            fi
        done < /tmp/pods.txt
        if [[ $cnt == $2 ]];then
            break
        fi
    done
}

waiting_ready() {
    while true
    do
        cnt=$(kubectl get pods | wc -l)
        if [[ $cnt == $READY_NO ]];then
            break
        fi
    done
}

wait_lb_ready() {
    while true
    do
        kubectl get svc  > /tmp/svcs.txt
        pending_flag=0
        while read line
        do
            if [[ $line == *"hdac-node"*"pending"* ]];then
                sleep 1
                pending_flag=1
                break
            fi
        done < /tmp/svcs.txt
        if [ $pending_flag -eq 0 ];then
            break
        fi
        echo "pending"
    done
}


#create namespace
kubectl create -f setup/fct-namespace.yaml
kubectl config set-context --current --namespace=fct
kubectl config get-contexts

#delete nodes
for i in $(seq 1 $FILE_NO)
do
    kubectl delete -f ./hdac-node-descs/hdac-node$i.yaml
done
cp ./hdac-node-descs/hdac-node-template.yaml /tmp
rm -rf ./hdac-node-descs/*
cp /tmp/hdac-node-template.yaml ./hdac-node-descs

#Grafana, Prometheus, CouchDB, hdac seed
kubectl delete -f ./couchdb-desc/couchdb.yaml
kubectl delete -f ./prometheus-desc/prometheus.yaml
kubectl delete -f ./grafana-desc/grafana.yaml
kubectl delete -f ./hdac-seed-desc/hdac-seed.yaml


NAME_ARRAY=()
i=0
kubectl get nodes > nodes.txt
while read line
do
    if [[ $line == *"NAME"* ]] || [[ $line == *"master"* ]];then
        continue
    fi
    NAME_ARRAY[$i]=$(echo $line | awk -F' ' '{print $1}')
    i=$((i + 1))
done < nodes.txt
KUBE_NODE_NO=$i

INDEX=0
cat ./couchdb-desc/couchdb-template.yaml | sed "s/{NODE_NAME}/${NAME_ARRAY[$INDEX]}/g" > ./couchdb-desc/couchdb.yaml
kubectl apply -f ./couchdb-desc/couchdb.yaml 
waiting_single "couchdb"

COUCHDB_IP=$(./get-public-ip.sh couchdb)
COUCHDB="http://admin:admin@$COUCHDB_IP:30598"

while true
do
    res=$(curl $COUCHDB)
    if [[ $res == *"Welcome"* ]];then
        break
    fi
done

#create couchDB
curl -X PUT $COUCHDB/seed-info
curl -X PUT $COUCHDB/wallet-address
curl -X PUT $COUCHDB/input-address
curl -X PUT $COUCHDB/seed-wallet-info

for i in {1..20}
do
    data=$(../hdacpy/make-wallet.py)
    curl -X PUT $COUCHDB/input-address/$i -d "$data"  
done 

INDEX=$((INDEX + 1))
cat ./hdac-seed-desc/hdac-seed-template.yaml | sed "s/{NODE_NAME}/${NAME_ARRAY[$INDEX]}/g" | sed "s/{TARGET}/${TARGET}/g" | sed "s/{WALLET_CNT}/\"$HDAC_NODE_NO_WITH_SEED\"/g" > ./hdac-seed-desc/hdac-seed.yaml
kubectl apply -f ./hdac-seed-desc/hdac-seed.yaml
waiting_single "hdac-seed" 

for i in $(seq 1 $HDAC_NODE_NO)
do
    INDEX=$((INDEX + 1))
    cat ./hdac-node-descs/hdac-node-template.yaml | sed "s/{NODE_NAME}/${NAME_ARRAY[$INDEX]}/g" | sed "s/{NO}/$i/g" | sed "s/{TARGET}/${TARGET}/g" | sed "s/{WALLET_ALIAS}/node$i/g" > ./hdac-node-descs/hdac-node$i.yaml
    kubectl apply -f ./hdac-node-descs/hdac-node$i.yaml
done

waiting_multi "hdac-node" $HDAC_NODE_NO
waiting_ready

#make prometheus config
cd prometheus-desc
./make-prometheus-config.sh
cd ..

#create configmap for prometheus-cubernetes
kubectl delete configmap prometheus-kubernetes
kubectl create configmap prometheus-kubernetes --from-file=./prometheus-desc/prometheus-kubernetes-config.yaml

INDEX=$((INDEX + 1))
cat ./prometheus-desc/prometheus-template.yaml | sed "s/{NODE_NAME}/${NAME_ARRAY[$INDEX]}/g" > ./prometheus-desc/prometheus.yaml
kubectl apply -f prometheus-desc/prometheus.yaml

NDEX=$((INDEX + 1))
cat ./grafana-desc/grafana-template.yaml | sed "s/{NODE_NAME}/${NAME_ARRAY[$INDEX]}/g" > ./grafana-desc/grafana.yaml
kubectl apply -f grafana-desc/grafana.yaml
    
cd ../hdacpy
if [ $1 == "friday" ];then
    ./test.sh 5
else
    ./test.sh 10
fi

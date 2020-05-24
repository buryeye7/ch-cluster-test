#!/bin/bash

PW="12345678"
kubectl get pods > /tmp/pods.txt
NAMES=()
INDEX=()
i=1
j=0
while read line
do
    if [[ $line == *"hdac-node"* ]];then
        mod=$((i%3))
        if [ $mod -eq 0 ];then
            NAMES[$j]=$(echo $line | awk -F' ' '{print $1}')
            INDEX[$j]=$i
            j=$((j+1))
        fi
        i=$((i+1))
    fi 
done < /tmp/pods.txt
NAME_CNT=$((j-1))

for i in $(seq 0 $NAME_CNT)
do
    j=$((i+1))
    pubkey=$(kubectl exec ${NAMES[$i]} --container hdac-node${INDEX[$i]} -- nodef tendermint show-validator)
    wallet_address=$(kubectl exec ${NAMES[$i]} --container hdac-node${INDEX[$i]} -- clif keys show node1 -a)
    expect -c "
    spawn kubectl exec ${NAMES[$i]} -it --container hdac-node${INDEX[$i]} -- clif hdac create-validator 1 --from $wallet_address --pubkey $pubkey --moniker solution --chain-id testnet
    expect "N]:"
        send \"y\\r\"
    expect "\'node1\':"
        send \"$PW\\r\"
    expect eof
    "
    sleep 10
    expect -c "
    spawn kubectl exec ${NAMES[$i]} -it --container hdac-node${INDEX[$i]} -- clif hdac bond --from node1 1 1 --chain-id testnet
    expect "N]:"
        send \"y\\r\"
    expect "\'node1\':"
        send \"$PW\\r\"
    expect eof
    "
done 

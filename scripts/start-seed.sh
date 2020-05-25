#!/bin/bash

COUCHDB="http://admin:admin@couchdb-app-svc:5984"
SRC="$GOPATH/src/friday"

ps -ef | grep nodef | while read line
do
    if [[ $line == *"gaiad"* ]];then
        target=$(echo $line |  awk -F' ' '{print $2}')
        kill -9 $target
    fi
done

#NODE_ID=$(nodef tendermint show-node-id)
IP_ADDRESS=$(hostname -I)
IP_ADDRESS=$(echo $IP_ADDRESS)

curl -X PUT $COUCHDB/seed-info/seed-info -d "{\"target\":\"${NODE_ID}@${IP_ADDRESS}:26656\"}"

for i in $(seq 1 $WALLET_CNT)
do
    wallet_address=$(gaiacli keys show node$i -a)
    curl -X PUT $COUCHDB/seed-wallet-info/$wallet_address -d "{\"wallet_alias\":\"node$i\"}"
done

#clif rest-server --laddr tcp://0.0.0.0:1317 > clif.txt 2>&1 &
gaiad start 

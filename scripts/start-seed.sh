#!/bin/bash

COUCHDB="http://admin:admin@couchdb-app-svc:5984"
PW="12345678"

mkdir -p $HOME/.gaiad
mkdir -p $HOME/.gaiacli

cp -rf $GOPATH/src/ch-cluster-test/config/gaiad-config/* $HOME/.gaiad
cp -rf $GOPATH/src/ch-cluster-test/config/gaiacli-config/* $HOME/.gaiacli
sed -i "s/prometheus = false/prometheus = true/g" $HOME/.gaiad/config/config.toml

gaiacli config chain-id testnet

ps -ef | grep gaiad | while read line
do
    if [[ $line == *"gaiad"* ]];then
        target=$(echo $line |  awk -F' ' '{print $2}')
        kill -9 $target
    fi
done

NODE_ID=$(gaiad tendermint show-node-id)
IP_ADDRESS=$(hostname -I)
IP_ADDRESS=$(echo $IP_ADDRESS)

curl -X PUT $COUCHDB/seed-info/seed-info -d "{\"target\":\"${NODE_ID}@${IP_ADDRESS}:26656\"}"

for i in $(seq 1 $WALLET_CNT)
do
    wallet_address=$(gaiacli keys show node$i -a)
    curl -X PUT $COUCHDB/seed-wallet-info/$wallet_address -d "{\"wallet_alias\":\"node$i\"}"
done

gaiad start 2>/dev/null &
sleep 20
gaiacli rest-server --chain-id=testnet --laddr tcp://0.0.0.0:1317 

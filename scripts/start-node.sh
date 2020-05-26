#!/bin/bash

COUCHDB="http://admin:admin@couchdb-app-svc:5984"
rm -rf $HOME/.gaiad
rm -rf $HOME/.gaiacli

ps -ef | grep gaiad | while read line
do
    if [[ $line == *"gaiad"* ]];then
        target=$(echo $line |  awk -F' ' '{print $2}')
        kill -9 $target
    fi
done

# run execution engine grpc server
gaiad init --chain-id testnet testnet

# create a wallet key
PW="12345678"

expect -c "
set timeout 3
spawn gaiacli keys add node
expect "disk:"
send \"$PW\\r\"
expect "passphrase:"
send \"$PW\\r\"
expect eof
"

cp -f $GOPATH/src/ch-cluster-test/config/gaiad-config/config/genesis.json $HOME/.gaiad/config

SEED=$(curl $COUCHDB/seed-info/seed-info | jq .target)
sed -i "s/seeds = \"\"/seeds = $SEED/g" $HOME/.gaiad/config/config.toml
sed -i "s/prometheus = false/prometheus = true/g" $HOME/.gaiad/config/config.toml

WALLET_ADDRESS=$(gaiacli keys show node -a)
NODE_PUB_KEY=$(gaiad tendermint show-validator)
NODE_ID=$(gaiad tendermint show-node-id)

curl -X PUT $COUCHDB/wallet-address/$WALLET_ADDRESS -d "{\"type\":\"full-node\",\"node_pub_key\":\"$NODE_PUB_KEY\",\"node_id\":\"$NODE_ID\", \"wallet_alias\":\"$WALLET_ALIAS\"}"

gaiad start 2>/dev/null &
sleep 20
gaiacli rest-server --chain-id=testnet --laddr tcp://0.0.0.0:1317 

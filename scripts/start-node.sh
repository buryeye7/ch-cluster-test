#!/bin/bash

COUCHDB="http://admin:admin@couchdb-app-svc:5984"
SRC="$GOPATH/src/friday"
rm -rf $HOME/.nodef/config
rm -rf $HOME/.nodef/data
rm -rf $HOME/.clif

ps -ef | grep grpc | while read line
do
    if [[ $line == *"CasperLabs"* ]];then
        target=$(echo $line |  awk -F' ' '{print $2}')
        kill -9 $target
    fi
done

ps -ef | grep nodef | while read line
do
    if [[ $line == *"nodef"* ]];then
        target=$(echo $line |  awk -F' ' '{print $2}')
        kill -9 $target
    fi
done

# run execution engine grpc server
$SRC/CasperLabs/execution-engine/target/release/casperlabs-engine-grpc-server -z -t 8 $HOME/.casperlabs/.casper-node.sock&

if [ $TARGET == "friday" ];then
    nodef init testnode friday --chain-id testnet
else
    nodef init testnode tendermint --chain-id testnet
fi

# create a wallet key
PW="12345678"

expect -c "
set timeout 3
spawn clif keys add node
expect "disk:"
    send \"$PW\\r\"
expect "passphrase:"
    send \"$PW\\r\"
expect eof
"

# apply default clif configure
clif config chain-id testnet
clif config output json
clif config indent true
clif config trust-node true

if [ $TARGET == "friday" ];then
    cp -f $GOPATH/src/friday-cluster-test/config/ulb-node-config/nodef-config/config/genesis.json $HOME/.nodef/config
    cp -f $GOPATH/src/friday-cluster-test/config/ulb-node-config/nodef-config/config/manifest.toml $HOME/.nodef/config
else
    cp -f $GOPATH/src/friday-cluster-test/config/node-config/nodef-config/config/genesis.json $HOME/.nodef/config
    cp -f $GOPATH/src/friday-cluster-test/config/node-config/nodef-config/config/manifest.toml $HOME/.nodef/config
fi

#SEED=$(cat $HOME/.nodef/config/genesis.json | jq .app_state.genutil.gentxs[0].value.memo)
SEED=$(curl $COUCHDB/seed-info/seed-info | jq .target)
sed -i "s/seeds = \"\"/seeds = $SEED/g" $HOME/.nodef/config/config.toml
sed -i "s/prometheus = false/prometheus = true/g" $HOME/.nodef/config/config.toml

WALLET_ADDRESS=$(clif keys show node -a)
NODE_PUB_KEY=$(nodef tendermint show-validator)
NODE_ID=$(nodef tendermint show-node-id)

curl -X PUT $COUCHDB/wallet-address/$WALLET_ADDRESS -d "{\"type\":\"full-node\",\"node_pub_key\":\"$NODE_PUB_KEY\",\"node_id\":\"$NODE_ID\", \"wallet_alias\":\"$WALLET_ALIAS\"}"

clif rest-server --laddr tcp://0.0.0.0:1317 > clif.txt 2>&1 &
nodef start 2>/dev/null

#!/bin/bash

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
$SRC/CasperLabs/execution-engine/target/release/casperlabs-engine-grpc-server -t 8 $HOME/.casperlabs/.casper-node.sock&

# init node
nodef init testnode --chain-id testnet

sed -i "s/prometheus = false/prometheus = true/g" ~/.nodef/config/config.toml

# copy execution engine chain configurations
cp $SRC/x/executionlayer/resources/manifest.toml ~/.nodef/config

# create a wallet key

PW="12345678"

expect -c "
set timeout 3
spawn clif keys add node1
expect "disk:"
send \"$PW\\r\"
expect "passphrase:"
send \"$PW\\r\"
expect eof
"
nodef add-genesis-account $(clif keys show node1 -a) 100000000stake
nodef add-el-genesis-account node1 "100000000000000000000000000000000000000" "1000000000000000000"

# add genesis node
nodef load-chainspec $HOME/.nodef/config/manifest.toml

# apply default clif configure
clif config chain-id testnet
clif config output json
clif config indent true
clif config trust-node true

# prepare genesis status
expect -c "
set timeout 3
spawn nodef gentx --name node1
expect "\'node1\':"
    send \"$PW\\r\"
expect eof
"

nodef collect-gentxs
nodef validate-genesis

cat $HOME/.nodef/config/genesis.json | jq .app_state.genutil.gentxs[0].value.memo > address.txt
#nodef start > nodef.txt

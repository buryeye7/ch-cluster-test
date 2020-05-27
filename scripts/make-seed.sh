#!/bin/bash

SRC="$GOPATH/src/friday"
rm -rf $HOME/.gaiad
rm -rf $HOME/.gaiacli

ps -ef | grep gaiad | while read line
do
    if [[ $line == *"gaiad"* ]];then
        target=$(echo $line |  awk -F' ' '{print $2}')
        kill -9 $target
    fi
done

# init node
gaiad init --chain-id testnet testnet
#sed -i "s/prometheus = false/prometheus = true/g" ~/.nodef/config/config.toml

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

for i in {1..100}
do
	expect -c "
	set timeout 3
	spawn gaiacli keys add node$i
	expect "disk:"
	send \"$PW\\r\"
	expect "passphrase:"
	send \"$PW\\r\"
	expect eof
	"
done

gaiad add-genesis-account node 1000000000stake,100000000000000000000uatom

expect -c "
set timeout 3
spawn gaiad gentx --name node
expect "\'node\':"
send \"$PW\\r\"
expect eof
"
gaiad collect-gentxs

#gaiad start

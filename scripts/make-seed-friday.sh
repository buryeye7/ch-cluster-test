#!/bin/bash

SRC="$GOPATH/src/friday"
rm -rf $HOME/.nodef
rm -rf $HOME/.clif

ps -ef | grep nodef | while read line
do
    if [[ $line == *"nodef"* ]];then
        target=$(echo $line |  awk -F' ' '{print $2}')
        kill -9 $target
    fi
done

# init node
nodef init --chain-id testnet testnet
#sed -i "s/prometheus = false/prometheus = true/g" ~/.nodef/config/config.toml

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

for i in {1..100}
do
	expect -c "
	set timeout 3
	spawn clif keys add node$i
	expect "disk:"
	send \"$PW\\r\"
	expect "passphrase:"
	send \"$PW\\r\"
	expect eof
	"
done

nodef add-genesis-account node 1000000000stake,100000000000000000000uatom

expect -c "
set timeout 3
spawn nodef gentx --name node
expect "\'node\':"
send \"$PW\\r\"
expect eof
"
nodef collect-gentxs

#nodef start

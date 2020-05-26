#!/usr/bin/python3

from cosmospy import Transaction
import sys
import requests
import json

#host="http://" + sys.argv[1] + ":1317/txs"
host="https://stargate.cosmos.network/txs"
#privkey=sys.argv[2]
privkey="ef10157a847bf6d99d25bc1c4b9c99c3230538ceaa918703a6fe50dd7c502071"
print("host " + host)
print("privkey " + privkey)


for i in range(10000):
        print("count", i)
        tx = Transaction(
                privkey=privkey,
                account_num=11335,
                sequence=i,
                fee=1000,
                gas=70000,
                memo="string",
                chain_id="testnet",
                sync_mode="sync"
            )
        amount = (i+1)%100
        try:
            tx.add_transfer(recipient="cosmos19t5wd4u9euv2etjgcqtjf3gg5v76j0m8rse8w8", amount=amount) 
            #tx.add_transfer(recipient="cosmos19t5wd4u9euv2etjgcqtjf3gg5v76j0m8rse8w8", amount=amount) 
            pushable_tx=tx.get_pushable().replace("uatom", "atom")
            fd=open("transfer-example.txt",'r')
            pushable_tx=json.dumps(json.loads(fd.read())).replace(" ","")
            headers = {'Content-Type': 'application/json'}
            print(pushable_tx)
            print("---")
            res=requests.post(host, headers=headers, data=pushable_tx)
            #res=requests.post(host, data=pushable_tx)
            print(res.status_code)
            print(res.text)
        except:
            print("exception happened", sys.exc_info()[0])
        

#!/usr/bin/python3

import sys
import requests
import json
from cosmospy import Transaction

#privkey="ef10157a847bf6d99d25bc1c4b9c99c3230538ceaa918703a6fe50dd7c502071"
#host="http://localhost:1317/txs"
host="http://" + sys.argv[1] + ":1317/txs"
privkey=sys.argv[2]
account_num=sys.argv[3]
print("host " + host)
print("privkey " + privkey)

i=0
#for i in range(10000):
while i < 10000:
        print("count", i)
        tx = Transaction(
                privkey=privkey,
                account_num=account_num,
                sequence=i,
                fee=1000,
                gas=70000,
                memo="",
                chain_id="testnet",
                sync_mode="sync"
            )
        amount = (i+1)%100 + 1
        try:
            tx.add_transfer(recipient="cosmos19t5wd4u9euv2etjgcqtjf3gg5v76j0m8rse8w8", amount=amount) 
            pushable_tx=tx.get_pushable()
            print(pushable_tx)
            headers = {'Content-Type': 'application/json; charset=utf-8'}
            res=requests.post(host, headers=headers, data=pushable_tx)
            #res=requests.post(host, data=pushable_tx)
            print(res.status_code)
            print(res.text)
            if not "code" in res.text:
                i += 1
        except:
            print("exception happened", sys.exc_info()[0])
        

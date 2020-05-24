#!/usr/bin/python3

from hdacpy.wallet import generate_wallet
from hdacpy.transaction import Transaction
import time
import sys


host="http://" + sys.argv[1] + ":1317"
privkey=sys.argv[2]
print("host " + host)
print("privkey " + privkey)
tx = Transaction(
        #host="http://afa42eb2e99ab11eaac7102613894823-106518416.ap-northeast-2.elb.amazonaws.com:1317",
        #privkey="367020ca5a8df01f852eee6ef3ecdd29d1d0057615be6ab29adf8ac6766dadc0",
        host=host,
        privkey=privkey,
        chain_id="testnet",
    )

for i in range(1,10000):
        print("count", i)
        amount = i%100
        try:
            tx.transfer(
                    recipient_address="friday19ktfw6flujxvxfnpgvldn4wj5mdx0565g6n4cj7zgshcfaxsyudsd9248t",
                    amount=amount, gas_price=30000000, fee=1
            )
        except:
            print("exception happened", sys.exc_info()[0])

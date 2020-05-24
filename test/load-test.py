#!/usr/bin/python3

from hdacpy.wallet import generate_wallet
from hdacpy.transaction import Transaction
import time

wallet = generate_wallet()
print(wallet)
"""
tx = Transaction(
        host="http://140.238.22.160:1317",
        privkey="8d4977704e623ee799515ee19eb5dddbaeaa22be0eee2431f83a742d38b2e928",
        chain_id="testnet",
    )

for i in range(1,10000):
        tx.transfer(
                recipient_address="friday1upwer8vatafqpc3m5kup4reuh3j6vknt74yamaq5lrgf0lapnm5smaj8xn",
                amount=i, gas_price=30000000, fee=1
        )
        print("count", i)
"""

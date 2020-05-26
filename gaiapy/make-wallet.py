#!/usr/bin/python3

from cosmospy import generate_wallet

wallet = generate_wallet()
#print(wallet)
dataList=[]
dataList.append(":".join(["\"private_key\"","\"" + wallet["private_key"] + "\""]))
dataList.append(":".join(["\"public_key\"","\"" + wallet["public_key"] + "\""]))
dataList.append(":".join(["\"address\"","\"" + wallet["address"] + "\""]))
data = "{" + ",".join(dataList) + "}"
print(data)

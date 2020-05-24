#!/bin/bash

NODE_NO=20
for i in $(seq 1 $NODE_NO)
do
    kubectl delete -f ./hdac-node-descs/hdac-node$i.yaml
done

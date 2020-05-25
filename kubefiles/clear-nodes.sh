#!/bin/bash

FILE_NO=$(ls -l hdac-node-descs | grep ^- | wc -l)
FILE_NO=$(($FILE_NO -1))
#delete nodes
for i in $(seq 1 $FILE_NO)
do
    kubectl delete -f ./gaia-node-descs/gaia-node$i.yaml
done
cp ./gaia-node-descs/gaia-node-template.yaml /tmp
rm -rf ./gaia-node-descs/*
cp /tmp/gaia-node-template.yaml ./gaia-node-descs

#Grafana, Prometheus, CouchDB, hdac seed
kubectl delete -f ./couchdb-desc/couchdb.yaml
kubectl delete -f ./prometheus-desc/prometheus.yaml
kubectl delete -f ./grafana-desc/grafana.yaml
kubectl delete -f ./hdac-seed-desc/hdac-seed.yaml

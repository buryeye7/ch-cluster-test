#!/bin/bash

rm tmp.txt
for i in {0..1000000}
do
    echo $i >> tmp.txt
    sleep 1
done

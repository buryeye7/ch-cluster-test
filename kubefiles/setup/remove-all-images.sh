#!/bin/bash

docker images | while read line
do
    if [[ "$line" == *"WARNING"* ]] || [[ "$line" == *"TAG"* ]];then
        continue
    fi    
    hash=$(echo $line | awk -F' ' '{print $3}')
    docker rmi -f $hash
done

#!/bin/bash

./kill-transfer-to.sh
rm transfer-to-log*
i=0
while read line
do
    param1=$(echo $line | awk -F' ' '{print $1}')
    param2=$(echo $line | awk -F' ' '{print $2}')
    ./transfer-to.py $param1 $param2 >> transfer-to-log$i.txt &    
    i=$((i + 1))
done < test-info-after-mempool-full.txt

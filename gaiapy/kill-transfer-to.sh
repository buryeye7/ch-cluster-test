#!/bin/bash

ps -ef | grep transfer | awk -F' ' '{print $2}' | while read line
do
    kill -9 $line
done


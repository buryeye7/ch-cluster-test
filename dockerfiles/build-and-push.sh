#!/bin/bash

cd hdac-seed
pwd
docker build --no-cache --tag buryeye7/hdac-seed:latest .
docker push buryeye7/hdac-seed:latest

cd ..
cd hdac-node
pwd
docker build --no-cache --tag buryeye7/hdac-node:latest .
docker push buryeye7/hdac-node:latest


#!/bin/bash

cd gaia-seed
pwd
docker build --no-cache --tag buryeye7/gaia-seed:latest .
docker push buryeye7/gaia-seed:latest

cd ..
cd gaia-node
pwd
docker build --no-cache --tag buryeye7/gaia-node:latest .
docker push buryeye7/gaia-node:latest


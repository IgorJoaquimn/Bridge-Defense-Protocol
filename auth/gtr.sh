#!/bin/bash

host="slardar.snes.2advanced.dev"
port="51001"
shift 2
command="gtr 1 2021032218:4:0150c1d3f97f9b397f63179d7fc66650617336d63e7e1c7c8b7968770b0549f1"

echo "python3 client.py $host $port $command"
# print the following line in the terminal
python client.py $host $port $command

echo " "

host="2001:12f0:601:a944:f21f:afff:fed5:967d"
echo "python3 client.py $host $port $command"
# print the following line in the terminal
python client.py $host $port $command
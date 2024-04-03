#!/bin/bash

host="2001:12f0:601:a944:f21f:afff:fed5:967d"
port="51001"
shift 2
command="itr 2021032218 4"

# Run the Python script with the provided arguments
python client.py $host $port $command



host="slardar.snes.2advanced.dev"
command="itr 2021032219 4"

# Run the Python script with the provided arguments
python client.py $host $port $command
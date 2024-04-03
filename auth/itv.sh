#!/bin/bash

host="2001:12f0:601:a944:f21f:afff:fed5:967d"
port="51001"
shift 2
command="itv 2021032218:4:461a7e4131a7658a6a2942780af9777d2f7914e2367e3afca8b71b0c9ac7a140"

# Run the Python script with the provided arguments
python client.py $host $port $command
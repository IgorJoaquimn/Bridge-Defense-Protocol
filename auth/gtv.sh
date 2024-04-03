#!/bin/bash

host="slardar.snes.2advanced.dev"
port="51001"
shift 2
command="gtv 2 2021032218:4:0150c1d3f97f9b397f63179d7fc66650617336d63e7e1c7c8b7968770b0549f1+2021032219:4:3a3a1ae527e58dec75ffd8b8f49652dbcc1814dfa0419baba2215d8c34c9bc7e+e04c49541cf3be0eff74f67896930825c2f5a25d46ebeb7cc8321817eb0adcd5"

# Run the Python script with the provided arguments
python client.py $host $port $command
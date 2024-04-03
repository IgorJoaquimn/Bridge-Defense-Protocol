import socket
import json
import time
from auth.client import auth

host = 'slardar.snes.2advanced.dev'
port = 51001
command = ["itr","2021032218",20]
token1  = auth(host,port,command)

command = ["itr","2021032218",20]
token2  = auth(host,port,command)

command = ["gtr",token1,token2]
token   = auth(host,port,command)


# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Example usage:
try:
    # Send a message
    message = {'auth': token, 'type': 'authreq'}
    json_message = json.dumps(message)
    sock.sendto(json_message.encode(), (host,port))

    data, addr = sock.recvfrom(1024)
    data =  json.loads(data.decode())
    print("Received message:", data)

except KeyboardInterrupt:
    print("Exiting...")
finally:
    sock.close()

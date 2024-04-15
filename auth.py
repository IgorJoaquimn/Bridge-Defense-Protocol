import socket
import json
import time
from auth.client import auth
from gamestate import GameState

host = 'pugna.snes.dcc.ufmg.br'
port = 51001 
command = ["itr","2021032218",20]
token1  = auth(host,port,command)

command = ["itr","2021031947",20]
token2  = auth(host,port,command)

command = ["gtr","2",token1,token2]
token   = auth(host,port,command)

g = GameState(host,51111,token=token)


g.authreq(token)
g.getcannons()

while(g.getturn()):
    g.quit()
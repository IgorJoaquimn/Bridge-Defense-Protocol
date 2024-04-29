import struct
import re
from auth.client import auth
from gamestate import GameState
import sys

args = sys.argv
host,port,gas = args[1:]

g = GameState(host,int(port),token=gas)

g.authreq()
g.getcannons()

while(g.getturn()):
    g.send_shot()
    g.turn += 1

g.quit()
print("Quantidade de barcos afundados: ",g.gameover["sunk_ships"])
print("Quantidade de barcos que escaparam: ",g.gameover["escaped_ships"])
print("Vida restante nos navios que escaparam: ",g.gameover["remaining_life_on_escaped_ships"])


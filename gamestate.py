from socket_t import *

class GameState:
    """ The GameState class is responsable send requests to the server and control the board"""

    def __init__(self,host,port,token = None):
        self.auth_token = None  
        self.token = token

        self.turn = 0 
        self.cannons = []
        self.state = []
        self.rivers = [River(i) for i in range(1,5)]

        self.sockets = [Socket(host,port+i) for i in range(4)]
        self.shot_list = []
    
    def __del__(self):
        """ Every socket created must be closed"""
        return self.quit()

    def authreq(self):
        """ A client starts a connection with the server sending an authentication request with type equal to authreq, passing in the (GAS):"""

        data = {}
        for sock in self.sockets: # Must send a requisition to every server
            try: # Error handling
                message = {'auth': self.token, 'type': 'authreq'}
                data = sock.sendto(message) # Stop and Wait
                self.auth_token = data["auth"]

            except KeyboardInterrupt:
                print("Exiting...")
            except GameOver as e:
                print("A error occurs...",e.message)
                self.quit()
                return self.authreq()

        return data
    
    def getcannons(self):
        """ Any server responds to a getcannons request with a response containing cannon placements. """

        data = {}
        try:
            message = {'auth': self.auth_token, 'type': 'getcannons'}
            data = self.sockets[0].sendto(message)
            self.cannons = data["cannons"]
        except ServerError as e:
            print("A error occurs...",e.message)
        
        return data

    def getturn(self):
        """ The client program should advance the state of the game by sending a getturn request to servers."""

        for i,sock in enumerate(self.sockets): # for every server
            try:
                message = {
                            "type": "getturn",
                            "auth": self.auth_token,  
                            "turn": self.turn
                            }

                states = sock.sendto(message) 
                for state in states: # process each state
                    for ship in state["ships"]: # save the corresponding river
                        ship["river"] = i 

                    self.rivers[i].ships[state["bridge"]-1] += state["ships"] # save the ships to the ith-river in the corresponding brigde

            except GameOver as e:
                return False # False means that something goes wrong with the requisition
        
        return states
    
    def quit(self):
        try:
            message = {'auth': self.auth_token, 'type': 'quit'}
            for sock in self.sockets:
                # Send quit message to each server
                sock.sendto(message)

        except KeyboardInterrupt:
            print("Exiting...")
        except GameOver as e:
            pass

    def get_possible_targets(self):
        """ Get the potential targets for each cannon. Fist check if there is a boat in the position """
        possible_targets = {}  
        for cannon in self.cannons:
            x, y = cannon  
            positions = set()  

            if y == 0:
                positions.add((x, 1))  # Cannon at y=0 can fire at river 1
            elif y == 4:
                positions.add((x, 4))  # Cannon at y=4 can fire at river 4
            else:
                positions.add((x, y - 1))  # Cannon can fire at the river above
                positions.add((x, y + 1))  # Cannon can fire at the river below
            

            # Get only the boats that are in a certain position
            for pos_x, pos_y in positions:
                river  = self.rivers[pos_y -1]
                ships = river.ships[pos_x -1]
                if(ships):
                    # Initialize possible_targets[x] if not exists
                    if x not in possible_targets:
                        possible_targets[x]    = {}
                    
                    if y not in possible_targets[x]:
                        possible_targets[x][y] = []

                    possible_targets[x][y] += ships
        return possible_targets
    
    def get_weakest_boat(self,boats):
        """ Get the boat that recieves least hits in a certain bridge."""

        life = {
            "frigate":	  1,
            "destroyer":  2,
            "battleship": 3
        } 

        weakest_boat = boats[0]
        weakest_boat["life"] = life[weakest_boat["hull"]] -  weakest_boat["hits"]
        
        for boat in boats:
            boat["life"] = life[boat["hull"]] -  boat["hits"]
            if boat["hits"] > weakest_boat["hits"]:
                weakest_boat = boat
        
        return weakest_boat
    
    def shot_strategy(self):
        """ Define the shotting strategy. Should return, to each cannon being fired, the cannon [x,y] and the id of the boat (x,y,id)
            Currently, shoot the first one
            """
        self.shot_list = []
        possible_targets = self.get_possible_targets()

        for x, y_dict in possible_targets.items():
            for y, boats in y_dict.items():
                 self.shot_list.append((x,y,self.get_weakest_boat(boats)))
        return self.shot_list

class River:
    def __init__(self, river_id):
        self.river_id = river_id  
        self.ships = [[] for i in range(8)]

    
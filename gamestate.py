from socket_t import *
import threading
from concurrent.futures import ThreadPoolExecutor as tpe
from concurrent.futures import as_completed

class GameState:
    """ The GameState class is responsable send requests to the server and control the board"""

    def __init__(self,host,port,token = None):
        self.auth_token = None  
        self.token = token

        self.turn = 0 
        self.cannons = []
        self.rivers = [River(i) for i in range(1,5)]

        self.host = host
        self.port = port
        self.sockets = [Socket(host,port+i) for i in range(4)]
        self.shot_list = []

        self.condition = threading.Condition()

        self.gameover = {}

    
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
                if("ongoing game" in e.data["description"]):
                    self.quit()
                    for s in self.sockets:
                        s.close()
                    self.sockets = [Socket(self.host,self.port+i) for i in range(4)]


                return self.authreq()

        return data
    
    def getcannons(self):
        """ Any server responds to a getcannons request with a response containing cannon placements. """

        data = {}
        try:
            message = {'auth': self.auth_token, 'type': 'getcannons'}
            data = self.sockets[0].sendto(message)
            self.cannons = data["cannons"]

            cannons = []

            for cannon in self.cannons:
                x, y = cannon  
                positions = []
                if y == 0:
                    positions.append((x, 1))  # Cannon at y=0 can fire at river 1
                elif y == 4:
                    positions.append((x, 4))  # Cannon at y=4 can fire at river 4
                else:
                    positions.append((x, y))  # Cannon can fire at the river above
                    positions.append((x, y + 1)) 
                obj = {}
                obj["x"] = x
                obj["y"] = y
                obj["pos"] = positions
                cannons.append(obj)
            self.cannons = cannons

        except ServerError as e:
            pass

        except GameOver as e:
            pass
        
        
        
        return data

    def getturn_one_server(self,i):
        try:
            message = {
                        "type": "getturn",
                        "auth": self.auth_token,  
                        "turn": self.turn
                        }
            
            self.rivers[i].ships = [[] for i in range(8)]

            states = self.sockets[i].sendto(message,8) 
            for state in states: # process each state
                for ship in state["ships"]: # save the corresponding river
                    ship["river"] = i 

                self.rivers[i].ships[state["bridge"]-1] += state["ships"] # save the ships to the ith-river in the corresponding brigde
        
        except GameOver as e:
            print(e.data)
            if( e.data['status']==0):
                self.gameover["sunk_ships"] = e.data['score']['sunk_ships']
                self.gameover["escaped_ships"] = e.data['score']['escaped_ships']
                self.gameover["remaining_life_on_escaped_ships"] = e.data['score']['remaining_life_on_escaped_ships']
            return False # False means that something goes wrong with the requisition
        
        return True
        
    def getturn(self):
        """ The client program should advance the state of the game by sending a getturn request to servers."""

        with tpe(max_workers=4) as executor:
            p_threads = []
            for i in range(len(self.sockets)):
                p_threads.append(executor.submit(self.getturn_one_server,i))

            goes_right = True
            for future in as_completed(p_threads):
                goes_right = goes_right and future.result()
    
        return goes_right
    
    def send_shot(self):

        self.shot_list = self.shot_strategy()

        threads = []

        for i in range(4):
            consumer_thread = threading.Thread(target = self.receive_shot,args=(i,))
            consumer_thread.start()
            threads.append(consumer_thread)

        while self.shot_list:
            with tpe(max_workers=5) as executor:
                p_threads = []
                with self.condition:
                    # make it using a pool of threads
                    for shot in self.shot_list:
                        # Create a new thread to process the request
                        p_threads.append(executor.submit(self.shot_message,shot))
                for thread in p_threads:
                    thread.result()

            with self.condition:
                self.condition.notify_all()

        with self.condition:
                self.condition.notify_all()

        for thread in threads:
            thread.join()

    def shot_message(self,shot):
        """ """
        x,y,id,river = shot
        try:
            message = {
                        "type": "shot",
                        "auth": self.auth_token,  
                        "cannon": [x,y],
                        "id": id
                        }

            self.sockets[river].send(message) 
            with self.condition:
                self.condition.notify_all()
             
        except:
            pass

    def receive_shot(self,river):
        while(self.shot_list):
            with self.condition:
                self.condition.wait()  # Wait until notified by the producer
                if(not self.shot_list): break
            
            
            response = self.sockets[river].listen()
            if(response and (response["type"] == "shotresp")):

                if(response["status"]!=0):
                    raise ServerError(message = "Shot gone wrong"+str(response))
                x,y = response["cannon"]
                id = response["id"]
                shot = (x,y,id,river)

                with self.condition:
                    if(shot in self.shot_list): self.shot_list.remove(shot)
            
                    
        while(self.sockets[river].listen() != None): continue
    
    def quit(self):
        try:
            message = {'auth': self.auth_token, 'type': 'quit'}
            for sock in self.sockets:
                # Send quit message to each server
                return sock.sendto(message)

        except KeyboardInterrupt:
            print("Exiting...")
        except GameOver as e:
            pass

    def get_possible_targets(self):
        """ Get the potential targets for each cannon. Fist check if there is a boat in the position """
        possible_targets = {}  
        for cannon in self.cannons:
            (x,y,pos) = cannon.values()
            # Get only the boats that are in a certain position
            for pos_x, pos_y in pos:
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
    
    def ship_not_in_shots(self,boat):
        # Iterar sobre a lista de tiros para verificar se algum tem o mesmo 'id'
        for (x,y,id,river) in self.shot_list:
            if id == boat['id']:
                return False  
        return True  
    
    def get_weakest_boat(self,boats):
        """ Get the boat that recieves least hits in a certain bridge."""

        life = {
            "frigate":	  1,
            "destroyer":  2,
            "battleship": 3
        } 

        safe_boat = boats[0]
        boats = [boat for boat in boats if self.ship_not_in_shots(boat)]

        if(not boats):
            return safe_boat
        
        weakest_boat = boats[0]
        weakest_boat["life"] = life[weakest_boat["hull"]] -  weakest_boat["hits"]
        
        for boat in boats:
            boat["life"] = life[boat["hull"]] -  boat["hits"]
            if (boat["life"] < weakest_boat["life"]):
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
                ship = self.get_weakest_boat(boats)
                self.shot_list.append((x,y,ship["id"],ship["river"]))
        return set(self.shot_list)

class River:
    def __init__(self, river_id):
        self.river_id = river_id  
        self.ships = [[] for i in range(8)]

    
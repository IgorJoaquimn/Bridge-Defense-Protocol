import socket
import json

class GameState:
    def __init__(self,host,port,token = None):
        self.auth_token = None  

        self.turn = 0 
        self.cannons = []
        self.state = []
        self.rivers = [River(i) for i in range(1,5)]

        self.sockets = [Socket(host,port+i) for i in range(4)]
        self.shot_list = []
    
    def __del__(self):
        return self.quit()

    def authreq(self,token=None):
        if((token == None)):
            token = self.token
        # Example usage:

        for sock in self.sockets:
            try:
                # Send a message
                message = {'auth': token, 'type': 'authreq'}
                data = sock.sendto(message)
                self.auth_token = data["auth"]

            except KeyboardInterrupt:
                print("Exiting...")
            except ServerError as e:
                print("A error occurs...",e.message)

        return data
    
    def getcannons(self):
        if(self.auth_token == None):
            self.auth_token = self.authreq(self.token)
        try:
            # Send a message
            message = {'auth': self.auth_token, 'type': 'getcannons'}
            data = self.sockets[0].sendto(message)
            self.cannons = data["cannons"]
        except ServerError as e:
            print("A error occurs...",e.message)
        
        return data

    def getturn(self):
        """ Get the current turn information in JSON format."""
        try:
            # Send a message
            message = {
                        "type": "getturn",  # Type of the message
                        "auth": self.auth_token,  # Authentication token
                        "turn": self.turn  # Current turn count
                        }

            states = self.sockets[0].sendto(message)

        except ServerError as e:
            print("A error occurs in getturn",e.message)
            return False
        
        return states
    
    def quit(self):
        try:
            message = {'auth': self.auth_token, 'type': 'quit'}
            for sock in self.sockets:
                # Send quit message to each server
                sock.sendto(message)

        except KeyboardInterrupt:
            print("Exiting...")
        except ServerError as e:
            pass

    def get_possible_targets(self):
        """ Get the potential targets for each cannon. Fist check if there is a boat in the position """
        possible_targets = {}  
        for cannon in self.cannons:
            x, y = cannon  
            targets = set()  

            if y == 0:
                targets.add((x, 1))  # Cannon at y=0 can fire at river 1
            elif y == 4:
                targets.add((x, 4))  # Cannon at y=4 can fire at river 4
            else:
                targets.add((x, y - 1))  # Cannon can fire at the river above
                targets.add((x, y + 1))  # Cannon can fire at the river below
            

            # Get only the boats that are in a certain position
            boats = []
            for boat_x, boat_y in targets:
                river  = self.rivers[boat_y]
                bridge = river.ships[boat_x]
                if(bridge):
                    boats.append((boat_x, boat_y,river.get_weakest_boat(boat_x)))

            possible_targets[cannon] = boats
        return possible_targets
    
    def shot_strategy(self):
        """ Define the shotting strategy. Should return, to each cannon being fired, the cannon [x,y] and the id of the boat (x,y,id)
            Currently, shoot the first one
            """
        self.shot_list = []
        possible_targets = self.get_possible_targets()
        for cannon in self.cannons:
            x, y, boat = possible_targets[cannon][0]
            self.shot_list.append((x,y,boat["id"]))
        return self.shot_list
    
    

class River:
    def __init__(self, river_id):
        self.river_id = river_id  
        self.ships = [[] for i in range(8)]

    def get_weakest_boat(self,bridge_id):
        """ Get the boat that recieves least hits in a certain bridge."""
        boats = self.ships[bridge_id]  
        weakest_boat = boats[0]
        
        for boat in boats:
            if boat["hits"] > weakest_boat["hits"]:
                weakest_boat = boat
        
        return weakest_boat


class Socket:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = self.create_socket()

    def create_socket(self):
        # Create a TCP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.1)
        return self.socket

    def sendto(self,message):
        # Example usage:
        try:
            json_message = json.dumps(message)
            self.socket.sendto(json_message.encode(), (self.host,self.port))
            responses = []
            while True:
                try:    
                    data, addr = self.socket.recvfrom(1024)
                    data =  json.loads(data.decode())
                    if(data["type"] == "gameover"):
                        raise ServerError("GameOver")
                    responses.append(data)
                except socket.timeout:
                    break

            if(len(responses) == 1):
                return responses[0]

            return responses

        except json.decoder.JSONDecodeError as e:
            print(e)
            print(data)
        return data


    def close(self):
        if self.socket:
            self.socket.close()

    def __del__(self):
        return self.close()




class ServerError(Exception):
    """Custom exception for authentication errors."""

    def __init__(self, message="Authentication failed"):
        self.message = message
        super().__init__(self.message)
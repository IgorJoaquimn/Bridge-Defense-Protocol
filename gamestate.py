class GameState:
    def __init__(self, auth_token):
        self.auth_token = auth_token  
        self.turn = 0 
        self.cannons = []
        self.state = []
        self.rivers = [River(i) for i in range(1,5)]

        self.shot_list = []

    def get_turn(self):
        """ Get the current turn information in JSON format."""
        return {
            "type": "getturn",  # Type of the message
            "auth": self.auth_token,  # Authentication token
            "turn": self.turn  # Current turn count
        }

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
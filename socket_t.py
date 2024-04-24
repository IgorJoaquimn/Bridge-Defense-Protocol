import socket
import json

class Socket:
    """ Class that implements the socket communication with builtin stop and wait."""
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = self.create_socket()

    def create_socket(self):
        # Create a TCP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.1)
        return self.socket
    
    def send(self,message):
        json_message = json.dumps(message)
        self.socket.sendto(json_message.encode(), (self.host,self.port))

    def listen(self):

        try:    
            data, addr = self.socket.recvfrom(1024)
            data =  json.loads(data.decode())
            if(data["type"] == "gameover"): 
                raise GameOver()
            return data
        
        except socket.timeout:
            return None
        
        except json.decoder.JSONDecodeError as e:
        # For some reason, some error messages from servers isin't json decodable, must investigate why
            if("gameover" in str(data)):
                raise GameOver()



    def sendto(self,message,n_responses=1):
        """ Principal method. Send a requisition and process the response. Uses stop-and-wait to be reliable"""

        response_type = {
            "authreq": "authresp",
            "getcannons": "cannons",
            "getturn": "state",
            "shot": "shotresp"
        }

        responses = []
        type = message["type"]
        json_message = json.dumps(message)
        self.socket.sendto(json_message.encode(), (self.host,self.port))
        while len(responses) < n_responses: 
        # While it can recieve something, recieves
            try:    
                data, addr = self.socket.recvfrom(2048)
                data =  json.loads(data.decode())
                if(data["type"] == "gameover"): 
                    raise GameOver()
                if(type == "quit"):
                    break
                if(data["type"] == response_type[type]):
                    responses.append(data)
                
            

            except socket.timeout:
            # Builtin stop-and-wait, if no previous data comes from the server in ONE timeout, must resend the message
                if(len(responses) != n_responses):
                    return self.sendto(message,n_responses)
            # Case the server already sended all its information, stops listening

            except json.decoder.JSONDecodeError as e:
            # For some reason, some error messages from servers isin't json decodable, must investigate why
                if("gameover" in str(data)):
                    raise GameOver()

        
        if(len(responses) == 1):
            return responses[0]

        return responses


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


class GameOver(ServerError):
    """Custom exception for GameOvers errors."""

    def __init__(self, message="GameOver"):
        self.message = message
        super().__init__(self.message)
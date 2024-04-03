import socket
from auth.messager import messager, RequestError, determine_ip_type, get_address_family_string
import sys
import struct


def auth(host,port,command):
    # Check if at least three arguments are provided (host, port, and command)
    # Extract host and port from command-line arguments
    host = str(host).strip()
    port = int(port)
    program_type = command[0]
    

    try: # Test if the program_type is valid
        messager_obj = messager(program_type=program_type)
    except Exception as e:
        raise e

    # Creating the socket object
    s = socket.socket(
        determine_ip_type(host),    # IPv6 
        socket.SOCK_DGRAM   # UDP
        )

    s.settimeout(404)

    # Try to connect with server and send a packet
    try:
        s.connect((host, port))
        packet = messager_obj.request(command[1:])

        # Send the packet to the server
        s.sendto(packet, (host, port))

        # Receive response from the server
        response, addr = s.recvfrom(4000)

        try: # Sanity test, if the an Error is provided by the server, the program stops
            messager_obj.check_error_message(response)

        except RequestError as e:
            raise e 
        
        # If isin't a error message, continue
        r = messager_obj.response(response)
        print(r)
        return r
        
    except socket.timeout:
        print("Timeout: No response received from the server. Resending request...")
        # Resend the request
        s.sendto(packet, (host, port))

    except Exception as e:
        print("Connection failed:", e)
        raise e

    # Closing the socket object
    s.close()
import struct
import re
import socket



ERROR_CODES = {
    1: "INVALID_MESSAGE_CODE - Sent when the client sent a request with an unknown type",
    2: "INCORRECT_MESSAGE_LENGTH - Sent when the client sent a request with incompatible size",
    3: "INVALID_PARAMETER - Sent when the server detects an error in any field of a request",
    4: "INVALID_SINGLE_TOKEN - Sent when one SAS in a GAS is invalid",
    5: "ASCII_DECODE_ERROR - Sent when a message contains a non-ASCII character"
}


class RequestError(Exception):
    def __init__(self, error_code):
        message = ERROR_CODES[error_code]
        self.message = message
        super().__init__(message)


class messager:
    def __init__(self, program_type):
        self.program_type = program_type
        methods = {
            "itv": (self.itv_request, self.itv_response),
            "itr": (self.itr_request, self.itr_response),
            "gtr": (self.gtr_request, self.gtr_response),
            "gtv": (self.gtv_request, self.gtv_response)
        }

        # Retrieve the request and response methods based on the program type
        try:
            self.request, self.response = methods[program_type]
        except KeyError:
            raise ValueError("Invalid program_type")
        

    def check_error_message(self, response):

        if(len(response) != 4): # A 4 bytes message is always an error
            return response

        error_message_format = '>HH'
        values = struct.unpack(error_message_format, response)
        raise RequestError(values[1])

    def parse_sas(self,sas):
        # Regular expression pattern to match the SAS format
        try:
            idd,nonce,token = sas.split(":")
            return idd,int(nonce),token
        except:
            raise ValueError("No id:nonce:token pattern found in the SAS")

    def itr_request(self, params):
        type_i = 1

        ID, nonce = params
        nonce = int(nonce)
        packet_format = ">H 12s I"


        packet = struct.pack(packet_format, 
            type_i, 
            bytes(ID, encoding="ascii"), 
            nonce
            )

        self.packet_format = packet_format
        return packet

    def itr_response(self, response):
        packet_format = ">2s 12s I 64s"
        values = struct.unpack(packet_format, response)

        ID, nonce, token = values[1:]
        ID = ID.decode("ascii")
        nonce = nonce
        token = token.decode("ascii")

        response = f"{ID}:{nonce}:{token}"
        return response

    def itv_request(self, params):
        ID,nonce,token = self.parse_sas(params[0])
        packet_format = ">H 12s I 64s"

        type_i = 3
        packet = struct.pack(packet_format, 
            type_i, 
            bytes(ID, encoding="ascii"), 
            nonce,
            bytes(token, encoding="ascii")
            )

        self.packet_format = packet_format
        return packet

    def itv_response(self,response):
        packet_format = ">2s 12s I 64s 1s"
        values = struct.unpack(packet_format, response)
        status = int(values[-1].decode() ==  b'\x01')
        return status

    def gtr_request(self, params):
        type_i = 5

        N = int(params[0])
        sass =  [self.parse_sas(p) for p in params[1:]]


        packet_format_sas = ">12s I 64s "
        sas_packets = [struct.pack(packet_format_sas,bytes(ID, encoding="ascii"),nonce,bytes(token, encoding="ascii")) for (ID,nonce,token) in sass]
        sas_packets = b''.join(sas_packets)
        packet_format = ">2s 2s"


        packet = struct.pack(packet_format, 
            type_i.to_bytes(2,"big"), 
            N.to_bytes(2,"big")
            ) +  sas_packets
        
        self.packet_format = (packet_format_sas * N).replace(">","")
        self.packet_format = ">H H " + self.packet_format
        return packet 

    def gtr_response(self,response):
        packet_format = self.packet_format + "64s"
        values = struct.unpack(packet_format, response)
        blocks = [values[i:i+3] for i in range(2, len(values)-2, 3)]
        sas = "+".join(f"{ID.decode('ascii')}:{nonce}:{token.decode('ascii')}" for (ID,nonce,token) in blocks)
        token = values[-1].decode('ascii')
        return sas + "+" + token

    def gtv_request(self, params):
        type_i = 7
        N = int(params[0])
        params = params[1].split("+")
        sass =  [self.parse_sas(p) for p in params[:-1]]
        token_g = params[-1]

        packet_format_sas = ">12s I 64s "
        sas_packets = [struct.pack(packet_format_sas,bytes(ID, encoding="ascii"),nonce,bytes(token, encoding="ascii")) for (ID,nonce,token) in sass]
        sas_packets = b''.join(sas_packets)
        packet_format = ">2s 2s"


        packet = struct.pack(packet_format, 
            type_i.to_bytes(2,"big"), 
            N.to_bytes(2,"big")
            ) + sas_packets + struct.pack("> 64s",bytes(token_g, encoding="ascii"))
        
        self.packet_format = (packet_format_sas * N).replace(">","")
        self.packet_format = ">2s 2s " + self.packet_format + "64s"
        return packet 

    def gtv_response(self,response):
        packet_format = self.packet_format + "1s"
        values = struct.unpack(packet_format, response)
        status = int(values[-1].decode() ==  b'\x01')
        return status



def determine_ip_type(hostname):
    ip_address = socket.getaddrinfo(hostname, None)[0][4][0]
    try:
        socket.inet_pton(socket.AF_INET, ip_address)
        return socket.AF_INET
    except socket.error:
        pass

    try:
        socket.inet_pton(socket.AF_INET6, ip_address)
        return socket.AF_INET6
    except socket.error:
        pass

    # If neither conversion succeeds, the resolved IP address is not a valid IPv4 or IPv6 address
    return None

def get_address_family_string(address_family):
    if address_family == socket.AF_INET:
        return "IPv4"
    elif address_family == socket.AF_INET6:
        return "IPv6"
    else:
        return "Unknown"
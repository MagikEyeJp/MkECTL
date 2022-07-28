import socket
import time
import sys
import json

class dobotController():
    def __init__(self ,param):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.basePos = {
            "x": param["posX"],
            "y": param["posY"],
            "z": param["posZ"],
            "r": param["posR"],
            "p": param["posP"]
        }
        self.targetPos = {
            "x": 0,
            "y": 0,
            "z": 0,
            "r": 0,
            "p": 0
        }
        self.host = param["hostName"]
        self.port = param["port"]

    def __del__(self):
        self.sock.close()

    def begin(self):
        try:
            self.sock.connect((self.host,self.port))
#        except Exception as e:
        except ConnectionRefusedError as e:
            print(f"{e}")
            return False
        else:
            return True

    def getPos(self):
        code = "M124"
        self.sock.send(code.encode())
        pos = json.loads(self.sock.recv(1024).decode())["body"][1]
        d = {
            "slider": pos["Z"],
            "pan": pos["R"],
            "tilt": pos["P"],
            "x": pos["X"],
            "y": pos["Y"]
        }
        return d

    def move(self,pos):

        if pos["x"] is not None:
            self.targetPos["x"] = pos["x"]
        if pos["y"] is not None:
            self.targetPos["y"] = pos["y"]
        if pos["slider"] is not None:
            self.targetPos["z"] = pos["slider"]
        if pos["pan"] is not None:
            self.targetPos["r"] = pos["pan"]
        if pos["tilt"] is not None:
            self.targetPos["p"] = pos["tilt"]

        print(pos)
        code = "G01"
        code += " X"+str(int(self.basePos["x"]-self.targetPos["x"]))
        code += " Y"+str(int(self.basePos["y"]-self.targetPos["y"]))
        code += " Z"+str(int(self.basePos["z"]-self.targetPos["z"]))
        code += " R"+str(int(self.basePos["r"]-self.targetPos["r"]))
        code += " P"+str(self.basePos["p"]-self.targetPos["p"])
        print(code)
        self.sock.send(code.encode())
        print(self.sock.recv(1024).decode())

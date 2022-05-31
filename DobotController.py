import socket
import time
import sys

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
        self.sock.connect((self.host,self.port))

    def move(self,pos):

        if pos["axis_x"] is not None:
            self.targetPos["x"] = pos["axis_x"]
        if pos["axis_y"] is not None:
            self.targetPos["y"] = pos["axis_y"]
        if pos["slider"] is not None:
            self.targetPos["z"] = pos["slider"]
        if pos["pan"] is not None:
            self.targetPos["r"] = pos["pan"]
        if pos["tilt"] is not None:
            self.targetPos["p"] = pos["tilt"]

        print(pos)
        code = "G00"
        code += " X"+str(int(self.basePos["x"]-self.targetPos["x"]))
        code += " Y"+str(int(self.basePos["y"]-self.targetPos["y"]))
        code += " Z"+str(int(self.basePos["z"]-self.targetPos["z"]))
        code += " R"+str(int(self.basePos["r"]+self.targetPos["r"]))
        code += " P"+str(self.basePos["p"]+self.targetPos["p"])
        print(code)
        self.sock.send(code.encode())
        time.sleep(1)
        print(self.sock.recv(1024).decode())
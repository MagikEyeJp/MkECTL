from enum import Enum, auto

class UIState():
    def __init__(self):
        self.machineFile:bool = None
        self.initialize:bool = None
        self.motor:bool = None
        self.irlight:bool = None
        self.sensor_connected:bool = None
        self.script:bool = None
        self.script_progress:bool = None


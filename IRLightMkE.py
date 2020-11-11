from IRLight import IRLight
import serial

class IRLightMkE(IRLight):

    def __init__(self, IRtype, IRdevice):
        # super(IRLight, self).__init__(parent)
        self.IRport = None

        self.type = IRtype
        self.device = IRdevice

    def open(self):
        self.IRport = serial.Serial(self.device)

        return 'Using ' + self.type


    def set(self, ch, state):
        cmd = ord('A') if state else ord('a')
        if 0 < ch < 3:
            cmd = cmd + ch - 1
        self.IRport.write(bytes([cmd]))


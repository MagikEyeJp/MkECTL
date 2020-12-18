from IRLight import IRLight
import serial

class IRLightMkE(IRLight):

    def __init__(self, IRtype, IRdevice):
        # super(IRLight, self).__init__(parent)
        self.IRport = None
        self.valid = False

        self.type = IRtype
        self.device = IRdevice

    def open(self):
        try:
            self.IRport = serial.Serial(self.device)
            self.valid = True
            msg = 'Using ' + self.type
        except serial.serialutil.SerialException:
            self.IRport = None
            self.valid = False
            msg = 'Open error ' + self.type
        return msg

    def isvalid(self) -> bool:
        return self.valid

    def set(self, ch, state):
        if self.valid:
            cmd = ord('A') if state else ord('a')
            if 0 < ch < 3:
                cmd = cmd + ch - 1
            self.IRport.write(bytes([cmd]))


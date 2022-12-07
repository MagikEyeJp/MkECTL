from IRLight import IRLight
import serial

class IRLightNumato(IRLight):

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
            if 0 < ch < 3:
                cmd = f"relay on {ch-1:d}\r" if state else f"relay off {ch-1:d}\r"
                print(cmd)
                print(cmd.encode('utf-8').hex())
                self.IRport.write(cmd.encode('utf-8'))

    def close(self):
        if self.IRport is not None:
            self.IRport.close()
        self.IRport = None
        self.valid = False

from IRLight import IRLight

import pty
import os
import serial

class IRLightDummy(IRLight):

    def __init__(self, IRtype, IRdevice):
        self.IRport = None

        self.type = IRtype
        self.device = IRdevice
    # https://stackoverflow.com/questions/2291772/virtual-serial-device-in-python


    def open(self):
        master, slave = pty.openpty()
        tty_dummy = os.ttyname(slave)
        self.device = tty_dummy
        self.IRport = serial.Serial(tty_dummy)

        return 'Using Dummy Lights'

    def set(self, ch, state):
        pass

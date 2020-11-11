from IRLight import IRLight

import pty
import os
import serial

class IRLightDummy(IRLight):

    def __init__(self):
        self.IRport = None

    # https://stackoverflow.com/questions/2291772/virtual-serial-device-in-python


    def open(self):
        master, slave = pty.openpty()
        tty_dummy = os.ttyname(slave)
        self.IRport = serial.Serial(tty_dummy)

        return 'Using Dummy Lights'

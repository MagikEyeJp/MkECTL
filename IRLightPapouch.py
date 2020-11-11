from IRLight import IRLight


from pathlib import Path
import os
import re
import serial

class IRLightPapouch(IRLight):

    def __init__(self, IRtype, IRdevice):
        self.IRport = None
        self.u2dTable = {}

        self.type = IRtype
        self.device = IRdevice

    def open(self):
        self.make_u2d_table()
        self.IRport = serial.Serial(self.u2dTable[self.device], 115200)

        return 'Using ' + self.type


    def set(self, ch, state):
        if 0 < ch < 3:
            # cmd = cmd + ch - 1
            if state:
                flag = 'H'
            else:
                flag = 'L'
            cmd = "*B1OS" + str(ch) + flag + "\r"
            # print(cmd, len(cmd), bytes(cmd, 'UTF-8'))
            self.IRport.write(bytes(cmd, 'UTF-8'))

    def make_u2d_table(self):
        p = Path('/sys/class/tty/')
        pfiles = list(p.glob("ttyUSB*"))
        print(pfiles)
        try:
            i = 1
            for d in pfiles:
                fulldir = os.path.realpath(d)
                print(fulldir)
                tksu = re.search(r"\d-\d\.\d[^/]*(?=:)", fulldir)
                tksd = re.search(r"ttyUSB\d+", fulldir)
                print(tksu, tksd)
                self.u2dTable[tksu[0]] = '/dev/' + tksd[0]
        except Exception as e:
            print(e)
        print(self.u2dTable)
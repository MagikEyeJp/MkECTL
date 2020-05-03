from math import pi
import KMControllersS
import os
import glob
from time import sleep

serials = {'pan': 'KM-1S K1UK#E45', 'tilt': 'KM-1S CBG3#573', 'slider': 'KM-1S SW59#0E9'}
scales = {'tilt': 2 * pi / 360.0, 'pan': 2 * pi / 360.0, 'slider': -2 * pi / 54.0}

def specifySN():
    # devices = []  # device name of motors
    devices = glob.glob(os.path.join('/dev', 'ttyUSB*'))

    motordic = {}

    for d in devices:
        motor = KMControllersS.USBController(d)
        # sleep(1.0)
        serialnum = motor.read_SN()  # Serial Number
        # print(d + ' : ' + str(serialnum))
        motordic[serialnum.decode()] = d
        motor.close()
        motor = None

    return motordic

# モータのID名から、対応するデバイス名を返す
# 引数がモータのID（文字列）、返り値がデバイス名とスケール
# motordic とmotorname  の紐付けしたい
def idToDeviceChar(id):

    motordic = specifySN()

    scale = 1.0
    dev = ''

    if id in serials:
        serialNum = serials[id]
        if serialNum in motordic:
            dev = motordic[serialNum]
            scale = scales[id]

    return dev, scale


def getMotorDic():
    # devices = []  # device name of motors
    devices = glob.glob(os.path.join('/dev', 'ttyUSB*'))

    motordic = {}

    for d in devices:
        motor = KMControllersS.USBController(d)
        # sleep(1.0)
        serialnum = motor.read_SN().decode()  # Serial Number
        if serialnum in serials.values():
            id = {v: k for k, v in serials.items()}[serialnum]  # https://note.nkmk.me/python-dict-swap-key-value/
            param = {}
            param['id'] = id
            param['cont'] = motor
            param['scale'] = scales[id]
            param['SN'] = serialnum
            motordic[id] = param

    return motordic




if __name__ == '__main__':
    print(specifySN())
    # print(idToDeviceChar('slider'))
    # print(idToDeviceChar('tilt'))
    # print(idToDeviceChar('pan')
    # print(idToDeviceChar('slir'))

from math import pi
import KMControllersS, KMControllersS_dummy
import os
import glob
from time import sleep
import re
import random

#serials = {'pan': 'KM-1S K1UK#E45', 'tilt': 'KM-1S CBG3#573', 'slider': 'KM-1S SW59#0E9', 'test': 'KM-1 CS9B#B12'}
#defaultSerials = {'pan': 'KM-1S 20BV#3A2', 'tilt': 'KM-1S 0D69#13A', 'slider': 'KM-1U 9PIG#CD1', 'test': 'KM-1 CS9B#B12'}
#defaultScales = {'tilt': -2 * pi / 360.0, 'pan': -2 * pi / 360.0, 'slider': -2 * pi / 59.97, 'test': 2 * pi / 54.0}
defaultMotors = {
    "slider": {
      "serial": "KM-1U 9PIG#CD1",
      "scale": -0.104772141
    },
    "pan": {
      "serial": "KM-1S 20BV#3A2",
      "scale": -0.017453293
    },
    "tilt": {
      "serial": "KM-1S 0D69#13A",
      "scale": -0.017453293
    }
}

def specifySN():
    # devices: list
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

    # if id in defaultSerials:
    #     serialNum = defaultSerials[id]
    #     if serialNum in motordic:
    #         dev = motordic[serialNum]
    #         scale = defaultScales[id]
    if id in defaultMotors:
        serialNum = defaultMotors[id]["serial"]
        if serialNum in motordic:
            dev = motordic[serialNum]
            scale = defaultMotors[id]["scale"]

    return dev, scale


def getMotorDic(motors=None):
    if motors is None:
        motors = defaultMotors

    serials = {k: v.get("serial") for k, v in motors.items()}
    scales = {k: v.get("scale") for k, v in motors.items()}

    motordic = {}
    calib_flag: bool = True

    devices = glob.glob(os.path.join('/dev', 'ttyUSB*'))
    if re.search('.+_dummy', random.choice(list(serials.values()))):  # dummy  devices: dictionary
        devices = ['slider', 'pan', 'tilt']  # pseudo port name = id
        calib_flag = False
        print("dummy mode.")
    else:   # real calibration
        pass
    # if 1 <= len(devices) <= 4:  # real calibration or test one
    #     print("real device mode.")
    #     pass
    # else:  # dummy  devices: dictionary
    #     devices = ['slider', 'pan', 'tilt']  # pseudo port name = id
    #     calib_flag = False
    #     print("dummy mode.")

    for d in devices:
        if calib_flag == True:  # real calibration or test one
            motor = KMControllersS.USBController(d)
            # sleep(1.0)
            serialnum = motor.read_SN().decode()  # Serial Number
            print(d, serialnum)
        else:  # dummy
            # serialnum = serials[d]
            # motor = KMControllersS_dummy.USBController(d, serialnum)
            motor = KMControllersS_dummy.USBController(d)
            serialnum = serials[d]
            print(d, serialnum)

        if serialnum in serials.values():
            id = {v: k for k, v in serials.items()}[serialnum]  # https://note.nkmk.me/python-dict-swap-key-value/
            param = {}
            param['id'] = id
            param['cont'] = motor
            param['scale'] = scales[id]
            param['SN'] = serialnum
            motordic[id] = param

            motor.set_scaling(scales[id], 0.0)  # offset = 0.0 (temp)

    return motordic


if __name__ == '__main__':
    # print(specifySN())
    print(getMotorDic())
    # print(idToDeviceChar('slider'))
    # print(idToDeviceChar('tilt'))
    # print(idToDeviceChar('pan')
    # print(idToDeviceChar('slir'))

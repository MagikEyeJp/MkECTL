
import os
import re  # https://qiita.com/luohao0404/items/7135b2b96f9b0b196bf3
import numpy as np
import datetime
import time
import math
from PyQt5 import QtWidgets

# import KMControllersS
import motordic

commands = {  # 'root': ['set_root', False],
            'set': ['set_img', False],
            'snap': ['snap_image', True],
            'mov': ['move_robot', True],
            # 'movs': ['movs_robot', False],
            # 'jog': ['jog_robot', False],
            'home': ['home_robot', False],
            'shutter': ['set_shutter', True],
            'gainiso': ['set_gainiso', True],
            'lasers': ['set_lasers', True],
            'light': ['set_light', True]
            }

app = QtWidgets.qApp

def execute_script(scriptName, devices, params):
    # print(commands['root'][0])
    f = open(scriptName)
    lines = f.read().splitlines()
    f.close()

    args_hist: list = []

    for line in lines:
        app.processEvents()
        if(len(line) == 0) or ("#" in line):  # (length of character = 0) or include "#"
            continue
            # https://stackoverflow.com/questions/44205923/checking-if-word-exists-in-a-text-file-python/44206026
            # print("This line is empty")

        # make list by split
        # https://stackoverflow.com/questions/6903557/splitting-on-first-occurrence
        com_args = line.split(" ", 1)
        com = com_args[0]
        if len(com_args) > 1:
            com_args[1] = com_args[1].replace(" ", "")  # del space
            com_args[1] = com_args[1].replace("\"", "")  # del double-quotation
            com_args[1] = com_args[1].split(",")
            if com_args[0] != 'set' and com_args[0] != 'snap':
                com_args[1] = np.array(com_args[1], dtype=int)
            elif com_args[0] == 'snap':
                com_args[1][1] = int(com_args[1][1])
            # print(type(com_args[1]))
            args = com_args[1]
        else:  # home
            args = np.array([0, 0, 0], dtype=int)
        # print(com_args)
        # print(commands[com_args[0]][0])

        eval(commands[com][0])(args, devices, params)  # https://qiita.com/Chanmoro/items/9b0105e4c18bb76ed4e9
        args_hist.append(args)

    # print(args_hist)
    # return args_hist

##########
def set_img(args, devices, params):
    print('---set_img---')

    now = datetime.datetime.now()
    dir_num: int = 1

    if not re.search('.+_image', args[0]):  # https://www.educative.io/edpresso/how-to-implement-wildcards-in-python
        print(args[0])
        print(type(args[0]))
        pass
    else:
        ymd = now.strftime('%Y%m%d')
        dir_path = str(ymd) + "_" + str(dir_num) + "/" + args[1].replace("/img_@{seqn}{4}_@{lasers}{4}_@{slide}{4}_@{pan}{4}_@{tilt}{4}.png","")
        print('var name: ' + str(args[0]))  # <- set var name as img_@...
        # if os.path.exists(str(ymd) + '.+'):
        while os.path.exists(dir_path):
            print('folder "' + dir_path + '" already exists')
            dir_num += 1
            dir_path = dir_path.replace(str(ymd) + "_" + str(dir_num - 1), str(ymd) + "_" + str(dir_num))

        os.makedirs(dir_path)  # https://note.nkmk.me/python-os-mkdir-makedirs/

def snap_image(args, devices, params):
    print('---snap_image---')

def move_robot(args, devices, params):
    print('---move_robot---')
    print('move to ' + str(args))
    motorSet = ['slider', 'pan', 'tilt']
    # params = motordic.getMotorDic()  # この処理消せる?

    for param_i in range(args.size):
        m = devices['motors'][motorSet[param_i]]
        scale = params[motorSet[param_i]]['scale']
        motorPos = args[param_i]

        m.moveTo(motorPos * scale)

        while True:
            time.sleep(0.2)
            app.processEvents()
            (pos, vel, torque) = m.read_motor_measurement()
            if math.fabs(pos - motorPos * scale) < 0.1:
                # print(pos)
                # print(torque)
                break

def home_robot(args, devices, params):
    print('---home_robot---')
    print('move to ' + str(args))
    move_robot(args, devices, params)

def set_shutter(args, devices, params):
    print('---set_shutter---')
    print('shatter speed: ' + str(args[0]))

def set_gainiso(args, devices, params):
    print('---set_gainiso---')
    print('gainiso: ' + str(args[0]))

def set_lasers(args, devices, params):
    print('---set_lasers---')
    if(args[0] == 1):
        print('laser : ON')
    else:
        print('laser : OFF')

def set_light(args, devices, params):
    print('---set_light---')
    if (args[1] == 1):
        print('light ' + str(args[0]) + ' : ON')
    else:
        print('light ' + str(args[0]) + ' : OFF')

    # # make folder ### https://tonari-it.com/python-split-splitlines/
    # if os.path.exists(line):
    #     print('フォルダ ' + line + ' は既に存在しています')
    # else:
    #     os.mkdir(line)

if __name__ == '__main__':
    execute_script('./script/script_2019-12-05_M_TOF_Archimedes_N=12_lendt=2.txt')
    # execute_script('script/demo.txt')

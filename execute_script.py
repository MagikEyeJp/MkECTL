
import os
import re  # https://qiita.com/luohao0404/items/7135b2b96f9b0b196bf3
import numpy as np
import datetime
import time
import math
import struct
import string
import itertools

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from PyQt5 import QtWidgets, QtGui
import scriptProgress_ui
import ini

# import KMControllersS
import motordic

# import mke-api
import pymkeapi

commands = {'root': ['set_root', False],
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
dynvars = {
            'seqn': 'd',
            'seqs': 'd',
            'shutter': 'd',
            'gainiso': 'd',
            'pan': 'd',
            'slide': 'd',
            'tilt': 'd',
            'lasers': 'd',
            'datetime': 't'
            }

app = QtWidgets.qApp

class ProgressWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ProgressWindow, self).__init__(parent)

        self.ui_script = scriptProgress_ui.Ui_script()
        self.ui_script.setupUi(self)

        self.done = 0
        self.total = 100
        self.percent = 0

        self.stopClicked = False

        # window position
        desktop = app.desktop()
        self.geometry = desktop.screenGeometry()
        # ウインドウサイズ(枠込)を取得
        self.framesize = self.frameSize()
        # ウインドウの位置を指定
        self.move(self.geometry.width() / 2 - self.framesize.width() / 2, self.geometry.height() / 2 - self.framesize.height() / 2)
        # self.move(self.geometry.width() / 2 - self.framesize.width(), self.geometry.height() / 2 - self.framesize.height() / 2)


        self.ui_script.progressLabel.setText(str(self.done) + ' / ' + str(self.total))
        self.ui_script.progressBar.setValue(self.percent)
        self.ui_script.stopButton.clicked.connect(self.interrupt)


    def updatePercentage(self):
        self.percent = self.done / self.total * 100
        # print(self.percent)
        self.ui_script.progressBar.setValue(self.percent)
        return self.percent

    def updateProgressLabel(self):
        self.ui_script.progressLabel.setText(str(self.done) + ' / ' + str(self.total))

    def interrupt(self):
        self.stopClicked = True
        self.close()

class Systate():
    def __init__(self):
        self.root = None
        self.dir_path: dict = {}
        # self.dir_path = ''
        self.saveFileName: dict = {}
        self.seqn: int = 0
        self.args = None
        self.skip = False
        self.now = datetime.datetime.now()
        self.ymd_hms = ''
        self.dir_num = 0
        self.folderCreated: dict = {}
        self.folderCreated = False

        self.past_parameters = Systate.PastParameters()

        self.pos = [0, 0, 0]
        self.shatter = 0
        self.gainiso = 0
        self.lasers = 0
        self.light = [0, 0]

    class PastParameters():
        def __init__(self):
            self.pos = [0, 0, 0]
            self.shatter = 0
            self.gainiso = 0
            self.lasers = 0
            self.light = [0, 0]


systate = Systate()

def execute_script(scriptParams, devices, params):
    global systate
    # devices: motors, lights, 3D sensors(sensor window)
    # params: motorDic

    # num of pictures

    # print(commands['root'][0])
    f = open(scriptParams.scriptName)
    lines = f.read().splitlines()
    f.close()

    progressBar = ProgressWindow()  # make an instance
    progressBar.total = len(lines)
    progressBar.updateProgressLabel()
    progressBar.show()

    args_hist: list = []

    for i, line in enumerate(lines):
        if progressBar.stopClicked:
            print('Interrupted')
            break

        print(' ########## ' + str(i) + '/' + str(len(lines)) + ' ########## ')


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
            if com_args[0] == 'set' or com_args[0] == 'root':
                pass
            elif com_args[0] == 'snap':
                com_args[1][1] = int(com_args[1][1])
            else:
                com_args[1] = np.array(com_args[1], dtype=int)
            # print(type(com_args[1]))
            args = com_args[1]
        else:  # home only
            args = np.array([0, 0, 0], dtype=int)

        systate.args = args

        systate.skip = commands[com][1]

        # GUI
        progressBar.ui_script.commandLabel.setText(com)

        # jump to a method(function)
        eval(commands[com][0])(systate.args, scriptParams, devices, params)  # https://qiita.com/Chanmoro/items/9b0105e4c18bb76ed4e9
        args_hist.append(args)

        # GUI
        progressBar.done = i
        progressBar.updateProgressLabel()
        progressBar.updatePercentage()

##########
def expand_dynvars(args, devices):
    print('---expand_dynvars---')
    global systate
    print('args : ' + str(args))

    ### @{a}{b}をaという変数についてb桁の数字に置き換える
    # https://note.nkmk.me/python-split-rsplit-splitlines-re/
    # https://note.nkmk.me/python-re-match-search-findall-etc/
    # https://userweb.mnet.ne.jp/nakama/

    for i in range(len(args)):
        if type(args[i]) != str:
            continue

        # fileName = systate.saveFileName[fileCategory]
        pattern = '_@\{([a-zA-Z_]\w*)\}\{([\w\d_\/\\:\-\+]+)\}'
        # dv_tokens = re.split(pattern, saveFileName[fileCategory])
        dv_tokens = re.split(pattern, args[i])

        if len(dv_tokens) < 2:
            continue    # temp

        dv_tokens = [n for n in dv_tokens if n!='']    # https://hibiki-press.tech/python/pop-del-remove/2871
        dv_tokens.pop(0)
        dv_tokens.pop(-1)   # https://note.nkmk.me/python-list-clear-pop-remove-del/
        dv_tokens = [dv_tokens[i:i + 2] for i in range(0, len(dv_tokens), 2)]   # https://www.it-swarm.dev/ja/python/python%E3%83%AA%E3%82%B9%E3%83%88%E3%82%92n%E5%80%8B%E3%81%AE%E3%83%81%E3%83%A3%E3%83%B3%E3%82%AF%E3%81%AB%E5%88%86%E5%89%B2/1047156094/

        for j in range(len(dv_tokens)):
            dv_name = dv_tokens[j][0]
            dv_par = int(dv_tokens[j][1])

            if not dv_name in dynvars:
                QtWidgets.QMessageBox.critical(devices['3Dsensors'], 'Cannot expand dynamic valuable', 'Unrecognized dynamic variable %s' % (dv_name))

            ### matlab
    #         if (dynvars{idx, 2} == 'd')
    #             dv_pard = str2double(dv_par);
    #             if (isnan(dv_pard))
    #                 errmsg = sprintf('Parameter of "%s" is not a number', dv_name);
    #                 return;
    #             end
    #         elseif(dynvars{idx, 2} == 't')
    #           try
    #                 datestr(now, dv_par);
    #           catch
    #           errmsg = sprintf('Parameter of "%s" in not a valid LDML string: %s', dv_name, dv_par);
    #           return;
    #          end
    #       end

            ### datetimeも後で追加
            if dv_name == 'seqn':
                dv_val = ('{:0=%d}' % (dv_par)).format(systate.seqn)
            elif dv_name == 'lasers':
                dv_val = ('{:0=%d}' % (dv_par)).format(devices['3Dsensors'].laserX)
            elif dv_name == 'shutter':
                dv_val = ('{:0=%d}' % (dv_par)).format(devices['3Dsensors'].shutterSpeed)
            elif dv_name == 'gainiso':
                dv_val = ('{:0=%d}' % (dv_par)).format(devices['3Dsensors'].gainiso)
            elif dv_name == 'slide':
                # dv_val = ('{:0=%d}' % (dv_par)).format(round(devices['motors']['slider'].m_position))
                dv_val = ('{:0=%d}' % (dv_par)).format(round(systate.pos_robots[0]))
            elif dv_name == 'pan':
                # dv_val = ('{:0=%d}' % (dv_par)).format(round(devices['motors']['pan'].m_position))
                dv_val = ('{:0=%d}' % (dv_par)).format(round(systate.pos_robots[1]))
            elif dv_name == 'tilt':
                # dv_val = ('{:0=%d}' % (dv_par)).format(round(devices['motors']['tilt'].m_position))
                dv_val = ('{:0=%d}' % (dv_par)).format(round(systate.pos_robots[2]))
            else:
                dv_val = 'xxxx'  # temp

            # fileName = fileName.replace('@{%s}{%d}' % (dv_name, dv_par), dv_val)
            args[i] = args[i].replace('@{%s}{%d}' % (dv_name, dv_par), dv_val)

        print('fileName : ' + args[len(args) - 1])
    # print(('zero padding: {:0=%d}' % (int(dv_tokens[1]))).format(seqn))   # https://note.nkmk.me/python-format-zero-hex/


##########

def set_root(args, scriptParams, devices, params):
    print('---set_root---')
    app.processEvents()
    global systate
    systate.root = args[0]


def set_img(args, scriptParams, devices, params):
    print('---set_img---')

    app.processEvents()
    global systate

    # ---------- make directory for images ----------
    # systate.now = datetime.datetime.now()
    systate.saveFileName[args[0]] = systate.args[1]
    print('systate.args[1] : ' + systate.args[1])

    if '_dots_destination' in args[0]:
        # temp
        pass
    else:
        # systate.ymd_hms = systate.now.strftime('%Y%m%d_%H%M%S')
        if args[0] == 'ccalib':
            # systate.dir_path[args[0]] = str(systate.ymd_hms) + "_" + str(systate.dir_num) + "/" + args[0]
            systate.dir_path[args[0]] = scriptParams.baseFolderName + '/' + scriptParams.subFolderName + "/" + args[0]
        else:
            # systate.dir_path[args[0]] = str(systate.ymd_hms) + "_" + str(systate.dir_num) + "/" + args[1].replace(
            #     "/img_@{seqn}{4}_@{lasers}{4}_@{slide}{4}_@{pan}{4}_@{tilt}{4}.png", "")
            systate.dir_path[args[0]] = scriptParams.baseFolderName + '/' + scriptParams.subFolderName + "/" + args[1].replace(
                "/img_@{seqn}{4}_@{lasers}{4}_@{slide}{4}_@{pan}{4}_@{tilt}{4}.png", "")
        print('var name: ' + str(args[0]))  # <- set var name as img_@...


        os.makedirs(systate.dir_path[args[0]])  # https://note.nkmk.me/python-os-mkdir-makedirs/
        # systate.folderCreated[args[0]] = True
        systate.folderCreated = True
    # ---------- make ini file ----------
    ini.generateIni(scriptParams.baseFolderName + '/' + scriptParams.subFolderName, scriptParams.scriptName)
    # ------------------------------

def snap_image(args, scriptParams, devices, params):
    print('---snap_image---')
    app.processEvents()
    global systate

    # im: QtGui.QPixmap() = None

    devices['3Dsensors'].frames = args[1]

    ### Save image
    fileName = []

    fileCategory = re.search('([a-zA-Z_]\w*)', args[0]).group()
    fileName.append(systate.saveFileName[fileCategory])
    expand_dynvars(fileName, devices)

    # devices['3Dsensors'].imgPath = systate.ymd_hms + '_' + str(systate.dir_num) + '/' + fileName[0]
    devices['3Dsensors'].imgPath = scriptParams.baseFolderName + '/' + scriptParams.subFolderName + '/' + fileName[0]
    # print(devices['3Dsensors'].imgPath)
    # devices['3Dsensors'].img.save(devices['3Dsensors'].imgPath)

    pixmap = devices['3Dsensors'].getImg(devices['3Dsensors'].frames)
    pixmap.save(devices['3Dsensors'].imgPath)

    systate.seqn += 1


def move_robot(args, scriptParams, devices, params):
    print('---move_robot---')
    print('move to ' + str(args))
    global systate
    motorSet = ['slider', 'pan', 'tilt']

    m = []
    scale = []
    motorPos = []
    pos = [0.0, 0.0, 0.0]
    vel = [0.0, 0.0, 0.0]
    torque = [0.0, 0.0, 0.0]
    Error = [0.0, 0.0, 0.0]
    Errors = 0.0
    # print(devices)

    for param_i in range(args.size):
        m.append(devices['motors'][motorSet[param_i]])
        scale.append(params[motorSet[param_i]]['scale'])
        motorPos.append(args[param_i])

    while True:
        for param_i in range(args.size):
            m[param_i].moveTo(motorPos[param_i] * scale[param_i])
            time.sleep(0.2)
            app.processEvents()

            (pos[param_i], vel[param_i], torque[param_i]) = m[param_i].read_motor_measurement()
            Error[param_i] = pow(pos[param_i] - motorPos[param_i] * scale[param_i], 2)
            Errors += Error[param_i]
            # print(Error[param_i])

        if math.sqrt(Errors) < 0.1:
                # print(pos)
                # print(torque)
                break
        Errors = 0.0

    time.sleep(1.0)

    systate.pos_robots = args


def home_robot(args, scriptParams, devices, params):
    print('---home_robot---')
    app.processEvents()
    global systate

    print('move to ' + str(args))
    move_robot(args, scriptParams, devices, params)

def set_shutter(args, scriptParams, devices, params):
    print('---set_shutter---')
    app.processEvents()
    global systate

    devices['3Dsensors'].shutterSpeed = args[0]
    print('shutter speed: ' + str(args[0]))
    # print('in 3D sensors: ' + str(devices['3Dsensors'].shutterSpeed))

    isOn = False
    for l in systate.light:
        if l > 0:
            isOn = True
            break

    ### Request to set shutter speed (args[0])
    m = scriptParams.IRonMultiplier if isOn else scriptParams.IRoffMultiplier
    devices['3Dsensors'].sensor.set_shutter(int(m * float(args[0]) + 0.5))

def set_gainiso(args, scriptParams, devices, params):
    print('---set_gainiso---')
    app.processEvents()
    global systate

    devices['3Dsensors'].gainiso = args[0]
    print('gainiso: ' + str(args[0]))

    ### Request to set gainiso (args[0])
    devices['3Dsensors'].sensor.set_gainiso(int(args[0]))

def set_lasers(args, scriptParams, devices, params):
    print('---set_lasers---')
    app.processEvents()
    global systate

    devices['3Dsensors'].laserX = args[0]

    ### Request to set lasers (args[0])
    devices['3Dsensors'].sensor.set_lasers(int(args[0]))


def set_light(args, scriptParams, devices, params):
    print('---set_light---')
    app.processEvents()
    global systate

    ch = int(args[0])

    cmd = ord('A') if int(args[1]) > 0 else ord('a')
    if 0 < ch < 3:
        cmd = cmd + ch - 1
        systate.light[ch - 1] = int(args[1])
        devices['lights'].write(bytes([cmd]))




if __name__ == '__main__':
    execute_script('./script/sampleScript1.txt')
    # execute_script('script/demo.txt')

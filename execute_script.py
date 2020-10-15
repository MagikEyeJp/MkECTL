
import os
import re  # https://qiita.com/luohao0404/items/7135b2b96f9b0b196bf3
import numpy as np
import datetime
import time
import math
import struct
import string
import itertools

from PyQt5 import QtWidgets, QtGui, QtCore
import scriptProgress_ui
import ini

# import KMControllersS
import motordic

# import mke-api
import pymkeapi

commands = {'root': ['set_root', False],
            'set': ['set_filename', False],
            'snap': ['snap_image', True],
            'snap3d': ['snap_3D_frame', True],
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

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self.interrupt()

    def closeEvent(self, event):  # https://www.qtcentre.org/threads/20895-PyQt4-Want-to-connect-a-window-s-close-button
        # self.deleteLater()
        # event.accept()
        self.interrupt()


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
        self.skip = False

        self.pos = [0, 0, 0]
        self.shutter = 0
        self.shutter_IRon = -1
        self.shutter_IRoff = -1
        self.gainiso = 0
        self.lasers = 0
        self.light = [0, 0]
        self.lightNum = 2

        self.past_parameters = Systate.PastParameters()
        self.sentSig = Systate.SentSig()

    class SentSig():
        def __init__(self):
            self.shutter = False
            self.gainiso = False
            self.pos = False
            self.lasers = False
            self.light = [False, False]


    class PastParameters():
        def __init__(self):
            self.pos = [0, 0, 0]
            self.shutter = 0
            self.gainiso = 0
            self.lasers = 0
            self.light = [0, 0]


systate = Systate()

def execute_script(scriptParams, devices, params):
    global systate
    systate.seqn = 0
    # devices: motors, lights, 3D sensors(sensor window)
    # params: motorDic

    f = open(scriptParams.scriptName)
    lines = f.read().splitlines()
    f.close()

    progressBar = ProgressWindow()  # make an instance

    args_hist: list = []
    com_hist: list = []

    warm_lasers(scriptParams, devices, params)

    # ---------- make ini file ----------
    # if scriptParams.isContinue:
    #     # ini.generateIni(scriptParams.baseFolderName + '/' + scriptParams.subFolderName, scriptParams.scriptName)
    #     if not os.path.exists(scriptParams.baseFolderName + '/'
    #                           + scriptParams.subFolderName + '/'
    #                           + 'Log.ini'):
    #         ini.updateIni_start(scriptParams.baseFolderName, scriptParams.subFolderName, scriptParams.scriptName, scriptParams.isContinue)
    # else:
    #     ini.updateIni_start(scriptParams.baseFolderName, scriptParams.subFolderName, scriptParams.scriptName, scriptParams.isContinue)
    ini.updateIni_start(scriptParams.baseFolderName, scriptParams.subFolderName, scriptParams.scriptName, scriptParams.isContinue)
    # ------------------------------

    for i, line in enumerate(lines):

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
            if com_args[0] == 'set' or com_args[0] == 'root' or com_args[0] == 'snap3d':
                pass
            elif com_args[0] == 'snap':
                com_args[1][1] = int(com_args[1][1])
            else:
                com_args[1] = np.array(com_args[1], dtype=float)
            # print(type(com_args[1]))
            args = com_args[1]
        else:  # home only
            args = np.array([0, 0, 0], dtype=int)

        args_hist.append(args)
        com_hist.append(com)

    for i in range(len(com_hist)):
        if progressBar.stopClicked:
            print('Interrupted')
            ini.updateIni_finish(scriptParams.baseFolderName + '/' + scriptParams.subFolderName, scriptParams.scriptName)

            return progressBar.stopClicked
            # break
        print(' ########## ' + str(i) + '/' + str(len(com_hist)) + ' ########## ')

        progressBar.stopClicked = False
        progressBar.total = len(com_hist)
        progressBar.updateProgressLabel()
        progressBar.show()

        systate.args = args_hist[i]
        systate.skip = commands[com_hist[i]][1]

        # GUI
        progressBar.ui_script.commandLabel.setText(com_hist[i])

        # jump to a method(function)
        eval(commands[com_hist[i]][0])(systate.args, scriptParams, devices, params)  # https://qiita.com/Chanmoro/items/9b0105e4c18bb76ed4e9

        # GUI
        progressBar.done = i
        progressBar.updateProgressLabel()
        progressBar.updatePercentage()

    ini.updateIni_finish(scriptParams.baseFolderName + '/' + scriptParams.subFolderName, scriptParams.scriptName)
    return True

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
                dv_val = ('{:0=%d}' % (dv_par)).format(systate.lasers)
            elif dv_name == 'shutter':
                dv_val = ('{:0=%d}' % (dv_par)).format(systate.shutter)
            elif dv_name == 'gainiso':
                dv_val = ('{:0=%d}' % (dv_par)).format(systate.gainiso)
            elif dv_name == 'slide':
                # dv_val = ('{:0=%d}' % (dv_par)).format(round(devices['motors']['slider'].m_position))
                dv_val = '{val:0{width}d}'.format(width=dv_par, val=int(systate.pos[0]))
            elif dv_name == 'pan':
                # dv_val = ('{:0=%d}' % (dv_par)).format(round(devices['motors']['pan'].m_position))
                dv_val = '{val:0{width}d}'.format(width=dv_par, val=int(systate.pos[1]))
            elif dv_name == 'tilt':
                # dv_val = ('{:0.0=%d}' % (dv_par)).format(round(devices['motors']['tilt'].m_position))
                dv_val = '{val:0{width}d}'.format(width=dv_par, val=int(systate.pos[2]))
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


def set_filename(args, scriptParams, devices, params):
    print('---set_filename---')

    app.processEvents()
    global systate

    # ---------- make directory for images ----------
    # systate.now = datetime.datetime.now()
    systate.saveFileName[args[0]] = systate.args[1]
    print('systate.args[1] : ' + systate.args[1])

    systate.dir_path[args[0]] = scriptParams.baseFolderName + '/' + scriptParams.subFolderName + "/" + os.path.dirname(args[1])

    if not os.path.exists(systate.dir_path[args[0]]):
        os.makedirs(systate.dir_path[args[0]])  # https://note.nkmk.me/python-os-mkdir-makedirs/
    # systate.folderCreated[args[0]] = True
    systate.folderCreated = True


def snap_image(args, scriptParams, devices, params):
    print('---snap_image---')
    app.processEvents()
    global systate

    # im: QtGui.QPixmap() = None

    devices['3Dsensors'].frames = int(args[1])

    ### Save image
    fileName = []

    fileCategory = re.search('([a-zA-Z_]\w*)', args[0]).group()
    fileName.append(systate.saveFileName[fileCategory])
    expand_dynvars(fileName, devices)

    # devices['3Dsensors'].imgPath = systate.ymd_hms + '_' + str(systate.dir_num) + '/' + fileName[0]
    devices['3Dsensors'].imgPath = scriptParams.baseFolderName + '/' + scriptParams.subFolderName + '/' + fileName[0]

    if not scriptParams.isContinue or not os.path.exists(devices['3Dsensors'].imgPath):
        resume_state(scriptParams, devices, params)
        time.sleep(0.2)

        image = devices['3Dsensors'].getImg(devices['3Dsensors'].frames)
        image.save(devices['3Dsensors'].imgPath)

    systate.seqn += 1
    warm_lasers(scriptParams, devices, params)

def snap_3D_frame(args, scriptParams, devices, params):
    print('---snap_3D_frame---')
    app.processEvents()
    global systate

    ### Save 3D frame
    fileName = []

    fileCategory = re.search('([a-zA-Z_]\w*)', args[0]).group()
    fileName.append(systate.saveFileName[fileCategory])
    expand_dynvars(fileName, devices)

    devices['3Dsensors'].csvPath = scriptParams.baseFolderName + '/' + scriptParams.subFolderName + '/' + fileName[0]

    if not scriptParams.isContinue or not os.path.exists(devices['3Dsensors'].csvPath):
        resume_state(scriptParams, devices, params)

        devices['3Dsensors'].snap3D(devices['3Dsensors'].csvPath)

    systate.seqn += 1

def move_robot(args, scriptParams, devices, params):
    print('---move_robot---')
    print('move to ' + str(args))
    global systate
    motorSet = ['slider', 'pan', 'tilt']

    args = np.array(args)

    m = []
    scale = []
    motorPos = []
    pos = [0.0, 0.0, 0.0]
    vel = [0.0, 0.0, 0.0]
    torque = [0.0, 0.0, 0.0]

    for param_i in range(args.size):
        m.append(devices['motors'][motorSet[param_i]])
        scale.append(params[motorSet[param_i]]['scale'])
        motorPos.append(args[param_i])

    systate.pos = motorPos

    if not systate.skip:
        if not systate.sentSig.pos or systate.pos != systate.past_parameters.pos:
            for param_i in range(args.size):
                m[param_i].moveTo(motorPos[param_i] * scale[param_i])

            while True:
                errors = 0.0
                for param_i in range(args.size):
                    time.sleep(0.2)
                    app.processEvents()
                    (pos[param_i], vel[param_i], torque[param_i]) = m[param_i].read_motor_measurement()
                    errors += pow(pos[param_i] - (motorPos[param_i] * scale[param_i]), 2)

                if math.sqrt(errors) < 0.1:
                    break

            systate.past_parameters.pos = systate.pos
            systate.sentSig.pos = True
            time.sleep(1.0)


def home_robot(args, scriptParams, devices, params):
    print('---home_robot---')
    app.processEvents()
    global systate

    # if not systate.skip:
    print('move to ' + str(args))
    move_robot(args, scriptParams, devices, params)


def set_shutter(args, scriptParams, devices, params):
    print('---set_shutter---')
    app.processEvents()
    global systate

    systate.shutter = int(args[0])

    if not systate.skip:
        isOn = False
        for l in systate.light:
            if l > 0:
                isOn = True
                break

        m = scriptParams.IRonMultiplier if isOn else scriptParams.IRoffMultiplier
        shutter = int(m * float(systate.shutter) + 0.5)
        if not systate.sentSig.shutter or shutter != systate.past_parameters.shutter:
            devices['3Dsensors'].shutterSpeed = shutter
            print('shutter speed: ' + str(shutter))

            ### Request to set shutter speed
            devices['3Dsensors'].sensor.set_shutter(shutter)

            systate.past_parameters.shutter = shutter
            systate.sentSig.shutter = True


def set_gainiso(args, scriptParams, devices, params):
    print('---set_gainiso---')
    app.processEvents()
    global systate

    systate.gainiso = int(args[0])

    if not systate.skip:
        if not systate.sentSig.gainiso or systate.gainiso != systate.past_parameters.gainiso:
            devices['3Dsensors'].gainiso = args[0]
            print('gainiso: ' + str(args[0]))

            ### Request to set gainiso (args[0])
            devices['3Dsensors'].sensor.set_gainiso(int(args[0]))

            systate.past_parameters.gainiso = systate.gainiso
            systate.sentSig.gainiso = True

def set_lasers(args, scriptParams, devices, params):
    print('---set_lasers---')
    app.processEvents()
    global systate

    systate.lasers = int(args[0])
    print('args=', args)

    if not systate.skip:
        if not systate.sentSig.lasers or systate.lasers != systate.past_parameters.lasers:
            devices['3Dsensors'].laserX = systate.lasers

            ### Request to set lasers (args[0])
            devices['3Dsensors'].sensor.set_lasers(systate.lasers)
            print('set_lasers(', systate.lasers, ")")

            systate.past_parameters.lasers = systate.lasers
            systate.sentSig.lasers = True


def set_light(args, scriptParams, devices, params):
    print('---set_light---')
    app.processEvents()
    global systate

    ch = int(args[0])
    print('ch=', ch, 'args=', args)

    systate.light[ch - 1] = int(args[1])

    if not systate.skip:
        if not systate.sentSig.light[ch - 1] or systate.light[ch - 1] != systate.past_parameters.light[ch - 1]:
            if 0 < ch < 3:
                systate.light[ch - 1] = int(args[1])
                cmd = ord('A') if int(args[1]) > 0 else ord('a')
                cmd = cmd + ch - 1
                devices['lights'].write(bytes([cmd]))
                # if int(args[1]) > 0:
                #     print('HIGH')
                #     flag = 'H'
                # else:
                #     print('LOW')
                #     flag = 'L'
                # cmd = bytes("*B1OS" + str(ch) + flag + "\r", 'UTF-8')
                # devices['lights'].write(cmd)
                systate.past_parameters.light[ch - 1] = systate.light[ch - 1]
                systate.sentSig.light[ch - 1] = True


def warm_lasers(scriptParams, devices, params):
    global systate
    current_skip = systate.skip
    current_lasers = systate.lasers
    current_shutter = systate.shutter

    print('---warm lasers---')
    systate.skip = False
    if systate.shutter_IRoff > 0:
        set_shutter([systate.shutter_IRoff], scriptParams, devices, params)
        print('  shutter=', systate.shutter_IRoff)
    set_lasers([255], scriptParams, devices, params)

    systate.skip = current_skip
    systate.lasers = current_lasers
    systate.shutter = current_shutter
    time.sleep(0.1)


def resume_state(scriptParams, devices, params):
    app.processEvents()
    global systate
    systate.skip = False

    for i in range(len(systate.light)):
        set_light([i + 1, systate.light[i]], scriptParams, devices, params)
    set_lasers([systate.lasers], scriptParams, devices, params)
    set_gainiso([systate.gainiso], scriptParams, devices, params)
    set_shutter([systate.shutter], scriptParams, devices, params)
    move_robot(systate.pos, scriptParams, devices, params)


# def snap_3D_frame():


if __name__ == '__main__':
    execute_script('./script/sampleScript1.txt')
    # execute_script('script/demo.txt')

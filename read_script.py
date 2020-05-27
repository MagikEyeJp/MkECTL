
import os
import re  # https://qiita.com/luohao0404/items/7135b2b96f9b0b196bf3
import numpy as np
import datetime
import time
import math
import struct
import string

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from PyQt5 import QtWidgets

# import KMControllersS
import motordic

# from mke-sdk
import pymkecli.client
import pymkecli.bus

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

# ------ from mke-sdk ------
# ------------------------------------------------------------------------------

REQUEST_GET_STATE = 20
REQUEST_SET_STATE = 21
REQUEST_GET_FRAME = 26
REPLY_OK = 200
STATE_IDLE = 1
STATE_DEPTH_SENSOR = 2

STATES = {STATE_IDLE:           'STATE_IDLE',
          STATE_DEPTH_SENSOR:   'STATE_DEPTH_SENSOR'}

# ------------------------------------------------------------------------------

def mke_send(conn, cmd, seq_id, params=bytes(8)):
    assert (len(params) == 8)  # params must have 8 bytes

    # assemble request

    req_header = b'MKERQ100'  # ASCII header of request
    cmd = bytes('%04d' % cmd, 'ascii')  # ASCII REQUEST_GET_STATE
    seq_id = struct.pack('<I', seq_id)  # binary sequence id
    request = req_header + cmd + seq_id + params
    # assembled whole request

    print("SENT:     %s %s %s %s" % (request[0:8], request[8:12], request[12:16], request[16:]))
    # nice print of whole request by parts

    # send datagram to device

    if conn.send(request) == 0:
        raise RuntimeError("Socket broken")


def mke_recv(conn, cmd, seq_id, exp_status):
    # wait for 48 bytes long reply

    reply = bytes()

    while len(reply) < 48:
        tmp = conn.recv(48)
        if len(tmp) == 0:
            raise RuntimeError("Socket closed");
        reply += tmp

    print(
        "RECEIVED: %s %s %s %s %s %s" % (reply[0:8], reply[8:12], reply[12:16], reply[16:20], reply[20:24], reply[24:]))
    # nice print of whole reply by parts

    # check reply

    assert (reply[0:8] == b'MKERP100')  # reply should start with header MKERP100
    assert (int(reply[8:12]) == cmd)  # command should be same
    assert (reply[16:20] == struct.pack('<I', seq_id))
    # sequence id should be same

    payload_size = struct.unpack('<I', reply[20:24])[0];

    # if there is some payload - read it

    while len(reply) < (48 + payload_size):
        tmp = conn.recv(payload_size)
        if len(tmp) == 0:
            raise RuntimeError("Socket closed");
        reply += tmp

    if payload_size > 0:
        print("PAYLOAD[%d bytes]:  %s" % (payload_size, reply[48:64] if len(reply) > 64 else reply[48:]))

    # check expected status code

    ret_code = int(reply[12:16])
    if ret_code != exp_status:
        raise RuntimeError("Reply with unexcepted status code %d" % ret_code)

    # return params and payload

    return (reply[24:48], reply[48:])

# ------------------------------------------------------------------------------


def execute_script(scriptName, devices, params):
    # devices: motors, lights, 3D sensors(sensor window)
    # params: motorDic

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

        # jump to a method(function)
        eval(commands[com][0])(args, devices, params)  # https://qiita.com/Chanmoro/items/9b0105e4c18bb76ed4e9
        args_hist.append(args)

    # print(args_hist)
    # return args_hist

##########
def set_img(args, devices, params):
    print('---set_img---')

    # ---------- make directory for images ----------
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
    # ------------------------------

    ### 正規表現の解読と、画像保存ルールを作る


def snap_image(args, devices, params):
    print('---snap_image---')
    app.processEvents()

    ### Request to get image

    ### Save image


def move_robot(args, devices, params):
    print('---move_robot---')
    print('move to ' + str(args))
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

def home_robot(args, devices, params):
    print('---home_robot---')
    app.processEvents()

    print('move to ' + str(args))
    move_robot(args, devices, params)

def set_shutter(args, devices, params):
    print('---set_shutter---')
    app.processEvents()

    devices['3Dsensors'].shutterSpeed = args[0]
    print('shutter speed: ' + str(args[0]))
    # print('in 3D sensors: ' + str(devices['3Dsensors'].shutterSpeed))

    ### Request to set shutter speed (args[0])


def set_gainiso(args, devices, params):
    print('---set_gainiso---')
    app.processEvents()

    devices['3Dsensors'].gainiso = args[0]
    print('gainiso: ' + str(args[0]))

    ### Request to set gainiso (args[0])


def set_lasers(args, devices, params):
    print('---set_lasers---')
    app.processEvents()

    ### Request to set lasers (args[0])



def set_light(args, devices, params):
    print('---set_light---')
    app.processEvents()

    if (args[1] == 1):
        try:
            # https://miyayamo.com/post-1924/
            devices['lights'].write(string.ascii_uppercase[args[0] - 1])  # A or B
        except Exception as e:
            print('cannot send serial ' + string.ascii_uppercase[args[0] - 1])
        print('light ' + str(args[0]) + ' : ON')
    else:
        try:
            devices['lights'].write(string.ascii_lowercase[args[0] - 1])  # a or b
        except Exception as e:
            print('cannot send serial ' + string.ascii_lowercase[args[0] - 1])
        print('light ' + str(args[0]) + ' : OFF')

    # # make folder ### https://tonari-it.com/python-split-splitlines/
    # if os.path.exists(line):
    #     print('フォルダ ' + line + ' は既に存在しています')
    # else:
    #     os.mkdir(line)


# ---------- from mke sdk ----------
def switch_to_depth_sensor(conn):
    # switch to STATE_DEPTH_SENSOR -----

    mke_send(conn, REQUEST_GET_STATE, 1)
    (params, payload) = mke_recv(conn, REQUEST_GET_STATE, 1, REPLY_OK)

    current_state = struct.unpack('<I', params[0:4])[0]

    assert (params[4:] == bytes(20))  # rest of params should be zero
    assert (len(payload) == 0)  # no payload expected

    # ------------------------------------------------------------------------------

    # if in IDLE go to DEPTH_SENSOR

    if current_state == STATE_IDLE:

        print('Switching to ', STATES.get(STATE_DEPTH_SENSOR))

        mke_send(conn, REQUEST_SET_STATE, 2, struct.pack('<I', STATE_DEPTH_SENSOR) + bytes(4))
        (params, payload) = mke_recv(conn, REQUEST_SET_STATE, 2, REPLY_OK)

        assert (params == bytes(24))  # no params expected
        assert (len(payload) == 0)  # no payload expected

        print('Device is in STATE_DEPTH_SENSOR.')

    else:
        print('Already in STATE_DEPTH_SENSOR');

    # ------------------------------------------------------------------------------


def get_frame(conn):
    # get one frame

    mke_send(conn, REQUEST_GET_FRAME, 3, struct.pack('<H', 1) + bytes(6))  # use FRAME_TYPE_2
    (params, payload) = mke_recv(conn, REQUEST_GET_FRAME, 3, REPLY_OK)

    # read params

    (timer, seqn, data_type, frame_type, num_data) = struct.unpack('<QQIHH', params)

    # prepare lists

    ids = []
    xs = []
    ys = []
    zs = []

    for i in range(num_data):
        sz = {1: 8, 2: 12}.get(frame_type)
        loc = payload[i * sz:(i + 1) * sz]

        ids.append(struct.unpack('<H', loc[0:2])[0])
        xs.append(struct.unpack('<h', loc[2:4])[0])
        ys.append(struct.unpack('<h', loc[4:6])[0])
        zs.append(struct.unpack('<h', loc[6:8])[0])

    # plot data

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.plot(xs, ys, zs, 'b.')
    plt.show()


def client_getframe(host, port):
    client = None

    try:
        bus = pymkecli.bus.TcpBus(host, port)
        client = pymkecli.client.SyncClient(bus)

        # go to state depth sensing

        state = client.get_state()
        print("Current state: %d" % state)

        if state != pymkecli.client.Api.STATE_DEPTH_SENSOR:
            print("Invalid state, let's change it")

            # firstly set state to IDLE
            if state != pymkecli.client.Api.STATE_IDLE:
                client.set_state(pymkecli.client.Api.STATE_IDLE)

            # then change state to DEPTH_SENSOR
            client.set_state(pymkecli.client.Api.STATE_DEPTH_SENSOR)

            # now the device is in DEPTH_SENSOR state
            print("Current state: %d" % client.get_state())
        else:
            print("Already in correct state.")

        # get one frame
        frame = client.get_frame(pymkecli.client.Api.FRAME_TYPE_1)

        # show the frame
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(frame.lut3d[:, 0], frame.lut3d[:, 1], frame.lut3d[:, 2], 'b.')
        plt.title("This is example of getting frame from MagikEye sensor.")
        plt.show()

        print("Correct termination");

    except Exception as e:
        print("An error occured: %s" % str(e))
    finally:
        if client:
            client.set_state(pymkecli.client.Api.STATE_IDLE)


def client_pushframes(host, port):
    client = None

    try:
        bus = pymkecli.bus.TcpBus(host, port)
        client = pymkecli.client.SyncClient(bus)

        # go to state depth sensing

        state = client.get_state()

        if state != pymkecli.client.Api.STATE_DEPTH_SENSOR:

            print("Invalid state, let's change it to DEPTH_SENSOR")

            # firstly set state to IDLE

            if state != pymkecli.client.Api.STATE_IDLE:
                client.set_state(pymkecli.client.Api.STATE_IDLE)

            # then change state to DEPTH_SENSOR

            client.set_state(pymkecli.client.Api.STATE_DEPTH_SENSOR)

        else:

            print("Already in correct state.")

        # main body ------------------------------------------------------------------

        # prepare figure

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        plt.ioff()
        fig.show()

        # prepare variables

        start_time = time.time()  # start of capturing
        timeout = 10  # when should be stop_frame_push called
        num = 0  # number of received images
        frame_type = 1  # used frame type

        # start pushing frames

        start_seq_id = client.start_frame_push(frame_type)
        stop_seq_id = None

        while True:

            # send stop push after num frames

            if stop_seq_id is None and (time.time() - start_time) >= timeout:
                stop_seq_id = client.stop_frame_push()

            # get next frame from the bus

            frame = client.get_pushed_frame(start_seq_id, stop_seq_id)

            # None denotes no more data

            if frame is None:
                print("Correctly finished loop")

                # all replies should be processed
                break

            # convert data and plot them

            ax.cla()
            ax.plot(frame.lut3d[:, 0], frame.lut3d[:, 1], frame.lut3d[:, 2], 'b.')
            plt.pause(0.001)

            num += 1

        print("Average displayed FPS: %.2f" % (num / (time.time() - start_time)))

        print("Correct termination");

    except Exception as e:
        print("An error occured: ", str(e))
    finally:
        if client:
            client.set_state(pymkecli.client.Api.STATE_IDLE)


if __name__ == '__main__':
    execute_script('./script/script_2019-12-05_M_TOF_Archimedes_N=12_lendt=2.txt')
    # execute_script('script/demo.txt')

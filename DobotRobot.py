from IRobotController import IRobotController
import socket
import json
import time
import numpy as np
import threading
from timeout_decorator import timeout, TimeoutError

MyType = np.dtype([(
    'len',
    np.int64,
), (
    'digital_input_bits',
    np.uint64,
), (
    'digital_output_bits',
    np.uint64,
), (
    'robot_mode',
    np.uint64,
), (
    'time_stamp',
    np.uint64,
), (
    'time_stamp_reserve_bit',
    np.uint64,
), (
    'test_value',
    np.uint64,
), (
    'test_value_keep_bit',
    np.float64,
), (
    'speed_scaling',
    np.float64,
), (
    'linear_momentum_norm',
    np.float64,
), (
    'v_main',
    np.float64,
), (
    'v_robot',
    np.float64,
), (
    'i_robot',
    np.float64,
), (
    'i_robot_keep_bit1',
    np.float64,
), (
    'i_robot_keep_bit2',
    np.float64,
), ('tool_accelerometer_values', np.float64, (3, )),
    ('elbow_position', np.float64, (3, )),
    ('elbow_velocity', np.float64, (3, )),
    ('q_target', np.float64, (6, )),
    ('qd_target', np.float64, (6, )),
    ('qdd_target', np.float64, (6, )),
    ('i_target', np.float64, (6, )),
    ('m_target', np.float64, (6, )),
    ('q_actual', np.float64, (6, )),
    ('qd_actual', np.float64, (6, )),
    ('i_actual', np.float64, (6, )),
    ('actual_TCP_force', np.float64, (6, )),
    ('tool_vector_actual', np.float64, (6, )),
    ('TCP_speed_actual', np.float64, (6, )),
    ('TCP_force', np.float64, (6, )),
    ('Tool_vector_target', np.float64, (6, )),
    ('TCP_speed_target', np.float64, (6, )),
    ('motor_temperatures', np.float64, (6, )),
    ('joint_modes', np.float64, (6, )),
    ('v_actual', np.float64, (6, )),
    # ('dummy', np.float64, (9, 6))])
    ('hand_type', np.byte, (4, )),
    ('user', np.byte,),
    ('tool', np.byte,),
    ('run_queued_cmd', np.byte,),
    ('pause_cmd_flag', np.byte,),
    ('velocity_ratio', np.byte,),
    ('acceleration_ratio', np.byte,),
    ('jerk_ratio', np.byte,),
    ('xyz_velocity_ratio', np.byte,),
    ('r_velocity_ratio', np.byte,),
    ('xyz_acceleration_ratio', np.byte,),
    ('r_acceleration_ratio', np.byte,),
    ('xyz_jerk_ratio', np.byte,),
    ('r_jerk_ratio', np.byte,),
    ('brake_status', np.byte,),
    ('enable_status', np.byte,),
    ('drag_status', np.byte,),
    ('running_status', np.byte,),
    ('error_status', np.byte,),
    ('jog_status', np.byte,),
    ('robot_type', np.byte,),
    ('drag_button_signal', np.byte,),
    ('enable_button_signal', np.byte,),
    ('record_button_signal', np.byte,),
    ('reappear_button_signal', np.byte,),
    ('jaw_button_signal', np.byte,),
    ('six_force_online', np.byte,),
    ('reserve2', np.byte, (82, )),
    ('m_actual', np.float64, (6, )),
    ('load', np.float64,),
    ('center_x', np.float64,),
    ('center_y', np.float64,),
    ('center_z', np.float64,),
    ('user[6]', np.float64, (6, )),
    ('tool[6]', np.float64, (6, )),
    ('trace_index', np.float64,),
    ('six_force_value', np.float64, (6, )),
    ('target_quaternion', np.float64, (4, )),
    ('actual_quaternion', np.float64, (4, )),
    ('reserve3', np.byte, (24, ))])

defaultAixs = ["X", "Y", "Z", "R", "P"]

def feedbakThread(obj):
    hasRead = 0
    while obj.isConnect:
        data = bytes()
        while hasRead < 1440:
            temp = obj.sockFeed.recv(1440 - hasRead)
            if len(temp) > 0:
                hasRead += len(temp)
                data += temp
        hasRead = 0

        a = np.frombuffer(data, dtype=MyType)
        if hex((a["test_value"][0])) == "0x123456789abcdef":

            # Refresh Properties
            current_actual = a["tool_vector_actual"][0]
            obj.currentPos = {list(obj.currentPos.keys())[i]:current_actual[i] for i in range(len(obj.currentPos))}

        time.sleep(0.001)


class DobotRobot(IRobotController):
    def __init__(self, machineParams=None):
        self.gwAddr = machineParams["gateway_addr"]
        self.gwPort = machineParams["gateway_port"]
        self.dobotAddr = machineParams["dobot_addr"]
        self.dobotPort = machineParams["dobot_port"]

        axes = machineParams["axes"]
        self.basePos = {axes[i]["axis"]: axes[i]["offset"] for i in axes.keys() if axes[i]["axis"] in defaultAixs }
        self.targetPos = {i:0 for i in self.basePos.keys()}
        self.currentPos = {i:0 for i in ["X","Y","Z","R"]}
        self.motorSet = [i for i in self.basePos.keys()]
        self.isConnect = False

    def connect(self, callback: callable = None, isAborted: callable = None):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sockFeed = socket.socket()
        try:
            self.isConnect = True
            self.sock.connect((self.gwAddr,self.gwPort))
            self.sockFeed.connect((self.dobotAddr, self.dobotPort))
            self.th = threading.Thread(target=feedbakThread,args=(self,),daemon=True)
            self.th.start()
        except ConnectionRefusedError as e:
            print(f"{e}")
            self.isConnect = False
            return False
        else:
            return True

    def initialize(self, callback: callable = None, isAborted: callable = None):
        return True

    def initializeOrigins(self, origins, callback: callable = None, isAborted: callable = None):
        return not self.moveTo({i:0 for i in self.basePos.keys()}, False, None, None )

    def getSettingWindow(self):
        pass

    def getPosition(self):
        code = "M124"
        self.sock.send(code.encode())
        pos = json.loads(self.sock.recv(1024).decode())["body"][1]
        return {i:self.basePos[i] - pos[i] for i in pos.keys()}

    def presetPosition(self, targetPos):
        pass

    def AsyncMoveTo(self, targetPos: dict, callback: callable, wait: bool = False, isAborted: callable = None, speed: int = None):
        """move to target position

        Move the robot to the target position.
        You can choose whether to wait until the move is complete.
        If this function is implemented as a blocking type, it should use callbacks to notify the caller of progress.

        :param targetPos: target position {"axis" : position_float ... }
        :param callback: callback function for status update and check abort request.
                         callback(position: dict, progress_now: int or float, progress_goal: int or float, allowAbort: bool = False}
                         position is same format of target position
                         The progress percentage should be displayed with progress_now / progress_goal
                         If allowAbort=True, isAbort will return True if there is an abort request.
        :param wait: If True, wait for the target position to reach exactly
        :param isAborted: A function to check whether there is an abort request

        :return: True if aborted
        """
        code = "G01"
        for i in self.basePos.keys():
            code += f" {i}{self.basePos[i] - targetPos[i]}" if i in targetPos.keys() else ""
        code += f" F{int(speed)}" if speed is not None else ""

        self.sock.send(code.encode())
        ret = json.loads(self.sock.recv(1024).decode())

        if not ret["status"] == 200:
            return True

        return False

    def moveTo(self, targetPos: dict, callback: callable, wait: bool = False, isAborted: callable = None):
        """move to target position

        Move the robot to the target position.
        You can choose whether to wait until the move is complete.
        If this function is implemented as a blocking type, it should use callbacks to notify the caller of progress.

        :param targetPos: target position {"axis" : position_float ... }
        :param callback: callback function for status update and check abort request.
                         callback(position: dict, progress_now: int or float, progress_goal: int or float, allowAbort: bool = False}
                         position is same format of target position
                         The progress percentage should be displayed with progress_now / progress_goal
                         If allowAbort=True, isAbort will return True if there is an abort request.
        :param wait: If True, wait for the target position to reach exactly
        :param isAborted: A function to check whether there is an abort request

        :return: True if aborted
        """
        code = "G00"
        for i in self.basePos.keys():
            code += f" {i}{self.basePos[i] - targetPos[i]}" if i in targetPos.keys() else ""

        self.sock.send(code.encode())
        ret = json.loads(self.sock.recv(1024).decode())

        if not ret["status"] == 200:
            return True

        @timeout(5)
        def waitmove():
            while True:
                time.sleep(0.01)
                is_arrive = True
                for i in targetPos.keys():
                    if i in self.currentPos.keys():
                        if abs( self.currentPos[i] - (self.basePos[i] - targetPos[i]) ) > 1:
                            is_arrive = False
                if is_arrive:
                    break

        try:
            waitmove()
        except TimeoutError as e:
            print(e)
            return True

        return False

    def freeMotors(self):
        pass

    def reboot(self):
        self.isConnect = False
        self.sock.close()
        self.th.join()
        self.sockFeed.close()

    def disconnect(self):
        self.isConnect = False
        self.sock.close()
        self.th.join()
        self.sockFeed.close()

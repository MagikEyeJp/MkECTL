from IRobotController import IRobotController
import socket

defaultAixs = ["X", "Y", "Z", "R", "P"]

class DobotRobot(IRobotController):
    def __init__(self, machineParams=None):
        self.gwAddr = machineParams["gateway_addr"]
        self.gwPort = machineParams["gateway_port"]

        axes = machineParams["axes"]
        self.basePos = {axes[i]["axis"]: axes[i]["offset"] for i in axes.keys() if axes[i]["axis"] in defaultAixs }
        self.targetPos = {i:0 for i in self.basePos.keys()}

    def connect(self, callback: callable = None, isAborted: callable = None):
        pass

    def initialize(self, callback: callable = None, isAborted: callable = None):
        pass

    def initializeOrigins(self, origins, callback: callable = None, isAborted: callable = None):
        pass

    def getSettingWindow(self):
        pass

    def getPosition(self):
        pass

    def presetPosition(self, targetPos):
        pass

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
        pass

    def freeMotors(self):
        pass

    def reboot(self):
        pass

    def disconnect(self):
        pass

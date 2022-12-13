
class IRobotController:
    def __init__(self, machineParams=None):
        pass

    def connect(self, callback: callable = None, isAborted: callable = None) -> bool:
        pass

    def initialize(self, callback: callable = None, isAborted: callable = None) -> bool:
        pass

    def initializeOrigins(self, origins: list = None, callback: callable = None, isAborted:callable = None) -> bool:
        pass

    def getSettingWindow(self) -> object:
        pass

    def getPosition(self) -> dict:
        pass

    def presetPosition(self, targetPos):
        pass

    def moveTo(self, targetPos: dict, callback: callable, wait: bool = False, isAborted: callable = None) -> bool:
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


class IRobotController:
    def __init__(self, machineParams=None):
        pass

    def connect(self, callback=None, isAborted=None):
        pass

    def initialize(self, callback=None, isAborted=None):
        pass

    def initializeOrigins(self, origins, callback=None, isAborted=None):
        pass

    def getSettingWindow(self):
        return None

    def getPosition(self):
        return None

    def presetPosition(self, targetPos):
        pass

    def moveTo(self, targetPos, callback, wait=False, isAborted=None, scriptParams=None, mainWindow=None):
        pass

    def freeMotors(self):
        pass

    def reboot(self):
        pass

    def disconnect(self):
        pass

from DobotController import dobotController

class Dobot():
    def __init__(self, machineParams_m=None):
        self.params = None
        self.machineParams = machineParams_m
        self.controller = dobotController(self.machineParams["dobot_conf"] if "dobot_conf" in self.machineParams else None)

    def setPrePos(self):
        self.controller.updateBasePos()

    def getMotorDic(self):
        self.params = {
            'slider': {
                'id': 'slider',
                'cont': "Controller object",
                'scale': 0,
                'SN': 'xxxxxxxxxxx'
            },
            'pan': {
                'id': 'pan',
                'cont': "Controller object",
                'scale': 0,
                'SN': 'xxxxxxxxxxx'
            },
            'tilt': {
                'id': 'tilt',
                'cont': "Controller object",
                'scale': 0,
                'SN': 'xxxxxxxxxxx'
            },
            'x':{
                'id':'x'
            },
            'y':{
                'id':'y'
            }
        }

    def getPosition(self):
        return self.controller.getPos()

    def reboot(self):
        self.controller.__del__()

    def initializeMotors(self):
        return self.controller.begin()

    def changePIDparam(self, pid_category, pid_param, motor_i, value):
        pass

    def goToTargetPos(self, targetPos, callback, wait=False, isAborted=None, scriptParams=None, mainWindow=None):
        self.controller.move(targetPos)
        return False


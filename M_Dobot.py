from IMotorRobot import IMotorRobot

class Dobot(IMotorRobot):
    def __init__(self, machineParams_m=None):
        self.params = None

    def getMotorDic(self):
        self.params = {
            'slider': {
                'id': 'x',
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
            }
        }

    def initializeMotors(self):
        return True

    def changePIDparam(self, pid_category, pid_param, motor_i, value):
        pass

    def goToTargetPos(self, targetPos, callback, wait=False, isAborted=None, scriptParams=None, mainWindow=None):
        True


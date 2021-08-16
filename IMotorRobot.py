
class IMotorRobot:

    def getMotorDic(self):
        pass

    def initializeMotors(self):
        pass

    def changePIDparam(self, pid_category, pid_param, motor_i, value):
        pass

    def goToTargetPos(self, targetPos, callback, wait=False, isAborted=None, scriptParams=None, mainWindow=None):
        pass

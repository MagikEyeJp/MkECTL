from IMotorRobot import IMotorRobot
from M_KeiganRobot import KeiganMotorRobot
from M_Dobot import Dobot

class RobotIF(IMotorRobot):
    def __init__(self, machineParams_m=None):
        if machineParams_m is None:
            machineParams_m = {}
        if 'calibrator_type' in machineParams_m:
                self.robotType = 'Dobot' if 'Dobot' == machineParams_m['calibrator_type'] else 'Keigan'
        else:
            self.robotType = 'Keigan'

        if self.robotType == 'Keigan':
            self.robot = KeiganMotorRobot(machineParams_m["motors"])
        else:
            self.robot = Dobot(machineParams_m)

        self.getMotorDic()
        self.params = self.robot.params

    def setPrePos(self):
        self.robot.setPrePos()

    def getMotorDic(self):
        self.robot.getMotorDic()

    def getPosition(self):
        return self.robot.getPosition()

    def reboot(self):
        self.robot.reboot()

    def initializeMotors(self):
        return self.robot.initializeMotors()

    def changePIDparam(self, pid_category, pid_param, motor_i, value):
        self.robot.changePIDparam(pid_category, pid_param, motor_i, value)
        pass

    def goToTargetPos(self, targetPos, callback, wait=False, isAborted=None, scriptParams=None, mainWindow=None):
        return self.robot.goToTargetPos(targetPos, callback, wait=False, isAborted=None, scriptParams=None, mainWindow=None)

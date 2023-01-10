import IRobotController
from KeiganRobot import KeiganRobot
from DobotRobot import DobotRobot
import IRLight
import IRLightDummy
import IRLightMkE
import IRLightNumato
import IRLightPapouch


def createRobot(params: dict) -> IRobotController:
    robot = None
    if isinstance(params, dict):
        typ = params.get('type')
        if typ == 'KEIGAN':
            robot = KeiganRobot(params.get('axes'))
        elif typ == 'DOBOT':
            robot = DobotRobot(params)
    return robot


def createLight(params: dict) -> IRLight:
    light = None
    if isinstance(params, dict):
        typ = params.get('type')
        device = params.get('device')
        if typ == 'MkE':
            light = IRLightMkE.IRLightMkE(typ, device)
        elif typ == 'PAPOUCH':
            light = IRLightPapouch.IRLightPapouch(typ, device)
        elif typ == 'Numato':
            light = IRLightNumato.IRLightNumato(typ, device)
        else: # dummy
            light = IRLightDummy.IRLightDummy(typ, device)
    return light


class Machine:
    class Axis:
        def __init__(self, name: str, unit: str, step: float, minvalue: float = -10000.0, maxvalue: float = 10000.0):
            self.name = name
            self.unit = unit
            self.step = step
            self.min = minvalue
            self.max = maxvalue

    def __init__(self):
        self.axes: [Machine.Axis] = []
        self.robot: IRobotController = None
        self.light: IRLight = None


class MachineBuilder:
    @staticmethod
    def build(machineParams: dict) -> Machine:
        # Analyze Machine Parameter
        machineFileVersion = machineParams.get("version", 1.0)
        machine = Machine()

        # build robot
        if machineFileVersion <= 1.0:
            # old machine file
            machine.axes = [Machine.Axis('slider', 'mm', 5.0), Machine.Axis('pan', 'deg', 0.1), Machine.Axis('tilt', 'deg', 0.1)]
            robot_params = machineParams.get('motors')
            if isinstance(robot_params, dict):
                machine.robot = KeiganRobot(robot_params)
            else:
                machine.robot = KeiganRobot()
        else:
            # v1.1 machine file
            machine.axes = []
            robot_params = machineParams.get('robot')
            if isinstance(robot_params, dict):
                machine.robot = createRobot(robot_params)
                params_axes = robot_params.get('axes')
                if machine.robot is not None and isinstance(params_axes, dict):
                    for a, d in params_axes.items():
                        axis = Machine.Axis(a, d.get('unit'), float(d.get('step')), float(d.get('min')), float(d.get('max')))
                        machine.axes.append(axis)
        #build light
        light_params = machineParams.get('IRLight')
        if isinstance(light_params, dict):
            machine.light = createLight(light_params)

        return machine


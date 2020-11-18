from enum import Enum, auto

class UIState(Enum):
    MACHINEFILE =       auto()
    INITIALIZE =        auto()
    MOTOR =             auto()
    IRLIGHT =           auto()
    SENSOR_CONNECTED =  auto()
    SCRIPT =            auto()
    SCRIPT_PROGRESS =   auto()


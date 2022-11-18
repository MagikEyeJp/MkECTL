from enum import Enum, auto

class UIState(Enum):
    MACHINEFILE =       auto()
    INITIALIZE =        auto()
    MOTOR =             auto()
    IRLIGHT =           auto()
    SCRIPT =            auto()
    SCRIPT_PROGRESS =   auto()


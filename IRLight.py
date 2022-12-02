
from abc import ABCMeta, abstractmethod

class IRLight(metaclass=ABCMeta):

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def isvalid(self) -> bool:
        pass

    @abstractmethod
    def set(self, ch, state):
        pass

    def close(self):
        pass

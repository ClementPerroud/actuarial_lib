from abc import ABC, abstractmethod
import random


class Service(ABC):
    def __hash__(self):
        return id(self).__hash__()
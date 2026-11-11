from abc import abstractmethod


class Dto:
    @abstractmethod
    def to_dict(self):
        pass

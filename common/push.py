from abc import abstractmethod


class PushMessage:

    @abstractmethod
    def send_single(self):
        pass

    @abstractmethod
    def send_broadcast(self):
        pass

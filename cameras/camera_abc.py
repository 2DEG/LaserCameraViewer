from abc import ABC, abstractmethod


def inheritors(klass):
    return {child.__name__: child for child in klass.__subclasses__()}


## Abstract camera class
class Camera_ABC(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def __new__(cls, backend, event_catcher=None, frame_queue=None):
        subclasses = inheritors(cls)
        if not backend in subclasses.keys():
            raise ValueError("Invalid backend '{}'".format(backend))
        subclass = subclasses[backend]
        instance = super(Camera_ABC, subclass).__new__(subclass)
        return instance

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def grab_frame(self):
        pass

    @abstractmethod
    def get_cam_id(self):
        pass

    @abstractmethod
    def set_exposure(self, exposure):
        pass

    @abstractmethod
    def set_gain(self, gain):
        pass

    @abstractmethod
    def get_exposure(self):
        pass

    @abstractmethod
    def get_gain(self):
        pass

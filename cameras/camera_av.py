import threading
import queue
import wx
from events.events import CAMImage, CAMParam, CAMInit
from cameras.camera_abc import *
from vmbpy import *

# All frames will either be recorded in this format, or transformed to it before being displayed
opencv_display_format = PixelFormat.Mono8

FRAME_HEIGHT = 1544 
FRAME_WIDTH = 2064

# FRAME_HEIGHT = 1080 
# FRAME_WIDTH = 1080


def print_all_features(module: FeatureContainer):
    for feat in module.get_all_features():
        print_feature(feat)
        # if feat.get_visibility() <= max_visibility_level:


def print_feature(feature: FeatureTypes):
    try:
        value = feature.get()

    except (AttributeError, VmbFeatureError):
        value = None

    print("/// Feature name   : {}".format(feature.get_name()))
    print("/// Display name   : {}".format(feature.get_display_name()))
    print("/// Tooltip        : {}".format(feature.get_tooltip()))
    print("/// Description    : {}".format(feature.get_description()))
    print("/// SFNC Namespace : {}".format(feature.get_sfnc_namespace()))
    print("/// Value          : {}\n".format(str(value)))


def get_value(cam: Camera, feat_name: str):
    val = None
    feat = cam.get_feature_by_name(feat_name)

    try:
        val = feat.get()
    except VmbFeatureError:
        print(
            "Camera {}: Failed to get value of Feature '{}'".format(
                cam.get_id(), feat_name
            )
        )

    if val:
        return val


def set_nearest_value(cam: Camera, feat_name: str, feat_value: int):
    # Helper function that tries to set a given value. If setting of the initial value failed
    # it calculates the nearest valid value and sets the result. This function is intended to
    # be used with Height and Width Features because not all Cameras allow the same values
    # for height and width.
    feat = cam.get_feature_by_name(feat_name)

    try:
        # min_, max_ = feat.get_range()
        feat.set(feat_value)

    except VmbFeatureError:
        print("Except in dimension setting")
        min_, max_ = feat.get_range()
        print("Dim range: ", min_, max_)
        inc = feat.get_increment()

        if feat_value <= min_:
            val = min_

        elif feat_value >= max_:
            val = max_

        else:
            val = (((feat_value - min_) // inc) * inc) + min_

        feat.set(val)

        msg = (
            "Camera {}: Failed to set value of Feature '{}' to '{}': "
            "Using nearest valid value '{}'. Note that, this causes resizing "
            "during processing, reducing the frame rate."
        )
        Log.get_instance().info(msg.format(cam.get_id(), feat_name, feat_value, val))


class Camera_AV(Camera_ABC, threading.Thread):
    """Class for Allied Vision cameras"""

    def __init__(self, *args, event_catcher=None, frame_queue=None, **kw):
        print("Here!")
        threading.Thread.__init__(self)
        self.command_queue = queue.Queue()
        self.producer = None
        self.event_catcher = event_catcher
        self.frame_queue = frame_queue

        try:
            with VmbSystem.get_instance() as vmb:
                for cam in vmb.get_all_cameras():
                    print("Cam ID:", cam.get_id())
                    with cam:
                        param_list = {
                            "gain": cam.Gain.get(),
                            "gain_range": cam.Gain.get_range(),
                            "gain_increment": cam.Gain.get_increment(),
                            "exposure": cam.ExposureTime.get(),
                            "exposure_range": cam.ExposureTime.get_range(),
                            "exposure_increment": cam.ExposureTime.get_increment(),
                            "height_range": cam.Height.get_range(),
                            "width_range": cam.Width.get_range(),
                        }
                        _, FRAME_HEIGHT = param_list["height_range"]
                        _, FRAME_WIDTH = param_list["width_range"]
                        print("Height, Width: ", FRAME_HEIGHT, FRAME_WIDTH)
                        wx.PostEvent(self.event_catcher, CAMInit(param_list))
        except VmbCameraError:
            pass

    def enum_cameras(self):
        cam_list = []
        print("Here!")
        with VmbSystem.get_instance() as vmb:
            for cam in vmb.get_all_cameras():
                cam_list.append(cam.get_id())
        
        if cam_list == []:
            return None, []

        return len(cam_list), cam_list

    class Producer(threading.Thread):
        def __init__(self, command_queue, event_catcher=None, frame_queue=None):
            threading.Thread.__init__(self)
            self.killswitch = threading.Event()
            self.event_catcher = event_catcher
            self.command_queue = command_queue
            self.frame_queue = frame_queue

        def __call__(self, cam: Camera, stream: Stream, frame: Frame):
            # This method is executed within VmbC context. All incoming frames
            # are reused for later frame acquisition. If a frame shall be queued, the
            # frame must be copied and the copy must be sent, otherwise the acquired
            # frame will be overridden as soon as the frame is reused.
            if frame.get_status() == FrameStatus.Complete:
                img = frame.convert_pixel_format(
                    opencv_display_format
                ).as_opencv_image()
                self.frame_queue.put(img)
                # wx.PostEvent(self.event_catcher, CAMImage(img))
            cam.queue_frame(frame)

        def stop(self):
            if self.isAlive():
                self.killswitch.set()
                self.join()

        def run(self):
            try:
                with VmbSystem.get_instance() as vmb:
                    for cam in vmb.get_all_cameras():
                        print(cam.get_id() == "DEV_1AB22C01054E")
                        with cam:
                            set_nearest_value(cam, "Height", FRAME_HEIGHT)
                            set_nearest_value(cam, "Width", FRAME_WIDTH)

                            try:
                                cam.start_streaming(self)
                                print("Streaming started")
                                while not self.killswitch.is_set():
                                    try:
                                        command, value = self.command_queue.get(
                                            timeout=0.1
                                        )  # One may use get_nowait() instead, but it is too fast, so one should handle queue.Empty
                                    except queue.Empty:
                                        continue
                                    else:
                                        if value is not None:
                                            set_nearest_value(cam, command, value)
                                        else:
                                            val = get_value(cam, command)
                                            if val:
                                                wx.PostEvent(
                                                    self.event_catcher,
                                                    CAMParam(command, val),
                                                )

                            finally:
                                cam.stop_streaming()
                                print("Streaming stopped")

                            print("Streaming ended")
            except VmbCameraError:
                pass

    def stop(self):
        self.producer.stop()
        if self.isAlive():
            self.join()

    def join(self, timeout=None):
        # self.stop()
        super().join(timeout)

    def run(self):
        self.producer = self.Producer(self.command_queue, self.event_catcher, self.frame_queue)
        self.producer.start()

    def get_cam_id(self):
        pass

    def set_exposure(self, exposure=200):
        self.command_queue.put(("ExposureTime", exposure))
        self.get_exposure()

    def set_gain(self, gain=1):
        self.command_queue.put(("Gain", gain))
        self.get_gain()

    def get_exposure(self):
        self.command_queue.put(("ExposureTime", None))

    def get_gain(self):
        self.command_queue.put(("Gain", None))

    def grab_frame(self, n=1):
        pass

import os
import sys
import logging
import threading
import queue
import wx
from events.events import CAMImage, CAMParam, CAMInit
from cameras.camera_abc import *

logger = logging.getLogger(__name__)

# Workaround: VmbPy's RuntimeTypeCheckEnable decorator calls
# typing.get_type_hints() which fails on Python 3.13+ due to stricter
# forward reference evaluation. Patch get_type_hints in the module so
# already-decorated functions use the safe version at call time.
if sys.version_info >= (3, 13):
    import vmbpy.util.runtime_type_check as _rtc
    _orig_get_type_hints = _rtc.get_type_hints

    def _safe_get_type_hints(func):
        try:
            return _orig_get_type_hints(func)
        except NameError:
            return {}

    _rtc.get_type_hints = _safe_get_type_hints

from vmbpy import *

# Known fallback paths for VimbaX CTI (transport layer) files
_VIMBAX_CTI_FALLBACKS = [
    r'C:\Program Files\Allied Vision\Vimba X\cti',
    r'C:\Program Files\Allied Vision\Vimba X\bin\cti',
]


def _get_vmb_instance():
    """Get VmbSystem instance with CTI path configuration.

    Uses the standard GENICAM_GENTL64_PATH environment variable if set.
    Otherwise falls back to known VimbaX installation paths.
    """
    vmb = VmbSystem.get_instance()
    if 'GENICAM_GENTL64_PATH' not in os.environ:
        for path in _VIMBAX_CTI_FALLBACKS:
            if os.path.isdir(path):
                vmb.set_path_configuration(path)
                break
    return vmb


# All frames will either be recorded in this format, or transformed to it before being displayed
opencv_display_format = PixelFormat.Mono8

FRAME_HEIGHT = 1544 
FRAME_WIDTH = 2064

# FRAME_HEIGHT = 1080 
# FRAME_WIDTH = 1080


def print_all_features(module: FeatureContainer):
    for feat in module.get_all_features():
        print_feature(feat)


def print_feature(feature: FeatureTypes):
    try:
        value = feature.get()
    except (AttributeError, VmbFeatureError):
        value = None

    logger.debug("Feature: %s = %s", feature.get_name(), value)


def get_value(cam: Camera, feat_name: str):
    val = None
    feat = cam.get_feature_by_name(feat_name)

    try:
        val = feat.get()
    except VmbFeatureError:
        logger.warning("Camera %s: Failed to get value of Feature '%s'",
                       cam.get_id(), feat_name)

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
        min_, max_ = feat.get_range()
        logger.debug("Feature '%s' range: %s - %s", feat_name, min_, max_)
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
        threading.Thread.__init__(self, daemon=True)
        self.command_queue = queue.Queue()
        self.producer = None
        self.event_catcher = event_catcher
        self.frame_queue = frame_queue

        try:
            with _get_vmb_instance() as vmb:
                for cam in vmb.get_all_cameras():
                    logger.info("Found camera: %s", cam.get_id())
                    try:
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
                            logger.info("Camera %s: resolution %dx%d", cam.get_id(), FRAME_WIDTH, FRAME_HEIGHT)
                            wx.PostEvent(self.event_catcher, CAMInit(param_list))
                    except (AttributeError, VmbFeatureError) as e:
                        logger.info("Skipping camera %s: %s", cam.get_id(), e)
                        continue
        except (VmbCameraError, VmbTransportLayerError):
            pass

    def enum_cameras(self):
        cam_list = []
        try:
            with _get_vmb_instance() as vmb:
                for cam in vmb.get_all_cameras():
                    cam_list.append(cam.get_id())
        except (VmbCameraError, VmbTransportLayerError):
            pass
        
        if cam_list == []:
            return None, []

        return len(cam_list), cam_list

    class Producer(threading.Thread):
        def __init__(self, command_queue, event_catcher=None, frame_queue=None):
            threading.Thread.__init__(self, daemon=True)
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
                try:
                    self.frame_queue.put_nowait(img)
                except queue.Full:
                    # Drop the oldest frame and enqueue the new one
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                    self.frame_queue.put_nowait(img)
            cam.queue_frame(frame)

        def stop(self):
            if self.is_alive():
                self.killswitch.set()
                self.join()

        def run(self):
            try:
                with _get_vmb_instance() as vmb:
                    for cam in vmb.get_all_cameras():
                        # Skip cameras that lack required features (e.g. virtual cameras)
                        try:
                            with cam:
                                set_nearest_value(cam, "Height", FRAME_HEIGHT)
                                set_nearest_value(cam, "Width", FRAME_WIDTH)

                                try:
                                    cam.start_streaming(self)
                                    logger.info("Streaming started on %s", cam.get_id())
                                    while not self.killswitch.is_set():
                                        try:
                                            command, value = self.command_queue.get(
                                                timeout=0.1
                                            )
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
                                    logger.info("Streaming stopped")

                                # Only stream from the first working camera
                                return
                        except (AttributeError, VmbFeatureError) as e:
                            logger.info("Skipping camera %s: %s", cam.get_id(), e)
                            continue
            except (VmbCameraError, VmbTransportLayerError):
                pass

    def stop(self):
        self.producer.stop()
        if self.is_alive():
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

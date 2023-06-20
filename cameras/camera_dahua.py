from cameras.dahua_crunches.ImageConvert import *
from cameras.dahua_crunches.MVSDK import *

# from cameras.dahua_crunches.utils import *
from cameras.camera_abc import *
import threading
import numpy
import gc

import wx
from events.events import CAMImage, CAMParam, CAMInit

g_cameraStatusUserInfo = b"statusInfo"


# DahuaCamera class inheriting from Camera_ABC
class DahuaCamera(Camera_ABC, threading.Thread):
    def __init__(self, *args, event_catcher=None, frame_queue = None, **kwargs):
        super().__init__()
        self.camera = None
        self.streamSource = None
        self.g_isStop = False
        self.event_catcher = event_catcher
        self.frame_queue = frame_queue
        self.gain_lock = threading.Lock()
        self.exposure_lock = threading.Lock()

    def run(self):
        self.open_camera()
        self.trigger_off()
        self.get_usb_info()
        self.start_grabbing()
        self.get_init_setup()

    def stop(self):
        self.stop_grabbing()
        self.close_camera()

    def grab_frame(self):
        if self.camera is not None:
            return self.get_frame()
        else:
            raise ValueError("Camera is not open.")

    def enum_cameras(self):
        """Returns a list of all available cameras"""
        system = pointer(GENICAM_System())
        nRet = GENICAM_getSystemInstance(byref(system))
        if nRet != 0:
            print("getSystemInstance fail!")
            return None, None

        cameraList = pointer(GENICAM_Camera())
        cameraCnt = c_uint()
        nRet = system.contents.discovery(
            system,
            byref(cameraList),
            byref(cameraCnt),
            c_int(GENICAM_EProtocolType.typeAll),
        )
        if nRet != 0:
            print("discovery fail!")
            return None, None
        elif cameraCnt.value < 1:
            print("discovery no camera!")
            return None, None
        else:
            print("cameraCnt: " + str(cameraCnt.value))
            return cameraCnt.value, cameraList

    def get_cam_id(self):
        if self.camera is not None:
            return str(self.camera.getSerialNumber(self.camera))
        else:
            raise ValueError("Camera is not open.")

    def set_exposure(self, exposure):
        if self.camera is not None:
            with self.exposure_lock:
                self.set_exposure_time(exposure)
            self.get_exposure()
        else:
            raise ValueError("Camera is not open.")

    def set_gain(self, gain):
        if self.camera is not None:
            with self.gain_lock:
                self.set_gain_value(gain)
            self.get_gain()
        else:
            raise ValueError("Camera is not open.")

    def get_exposure(self):
        if self.camera is not None:
            with self.exposure_lock:
                exp = self.get_exposure_time()
                wx.PostEvent(
                    self.event_catcher,
                    CAMParam("ExposureTime", exp),
                )
                return exp
        else:
            raise ValueError("Camera is not open.")

    def get_gain(self):
        if self.camera is not None:
            with self.gain_lock:
                gain = self.get_gain_value()
                wx.PostEvent(
                    self.event_catcher,
                    CAMParam("Gain", gain),
                )
                return gain
        else:
            raise ValueError("Camera is not open.")

    def open_camera(self):
        # Discover cameras
        cameraCnt, cameraList = self.enum_cameras()

        if cameraCnt is None or cameraCnt == 0:
            raise ValueError("No cameras found.")

        # Open the first camera
        self.camera = cameraList[0]

        # Connect to the camera
        nRet = self.camera.connect(
            self.camera, c_int(GENICAM_ECameraAccessPermission.accessPermissionControl)
        )
        if nRet != 0:
            raise ValueError("Failed to connect to the camera.")

        # Register camera connection status callbacks
        nRet = self.subscribe_camera_status()
        if nRet != 0:
            raise ValueError("Failed to subscribe to camera status notifications.")

    def close_camera(self):
        # Unregister camera connection status callbacks
        nRet = self.unsubscribe_camera_status()
        if nRet != 0:
            raise ValueError("Failed to unsubscribe from camera status notifications.")

        # Disconnect from the camera
        nRet = self.camera.disConnect(byref(self.camera))
        if nRet != 0:
            raise ValueError("Failed to disconnect from the camera.")

        self.camera = None

    def start_grabbing(self):
        if self.camera is None:
            raise ValueError("Camera is not open.")

        # Create stream object
        streamSourceInfo = GENICAM_StreamSourceInfo()
        streamSourceInfo.channelId = 0
        streamSourceInfo.pCamera = pointer(self.camera)

        self.streamSource = pointer(GENICAM_StreamSource())
        nRet = GENICAM_createStreamSource(
            pointer(streamSourceInfo), byref(self.streamSource)
        )
        if nRet != 0:
            raise ValueError("Failed to create stream source.")

        # Attach grabbing callback
        userInfo = b"test"
        self.attach_callback = callbackFuncEx(self.on_get_frame)
        nRet = self.streamSource.contents.attachGrabbingEx(
            self.streamSource, self.attach_callback, userInfo
        )
        if nRet != 0:
            raise ValueError("Failed to attach grabbing callback.")

        # Start grabbing
        nRet = self.streamSource.contents.startGrabbing(
            self.streamSource,
            c_ulonglong(0),
            c_int(GENICAM_EGrabStrategy.grabStrartegySequential),
        )
        if nRet != 0:
            raise ValueError("Failed to start grabbing.")

        self.g_isStop = False

    def stop_grabbing(self):
        if self.streamSource is None:
            raise ValueError("Stream source is not initialized.")

        self.g_isStop = True

        # Detach grabbing callback
        nRet = self.streamSource.contents.detachGrabbingEx(
            self.streamSource, self.attach_callback, b"test"
        )
        if nRet != 0:
            raise ValueError("Failed to detach grabbing callback.")

        # Stop grabbing
        nRet = self.streamSource.contents.stopGrabbing(self.streamSource)
        if nRet != 0:
            raise ValueError("Failed to stop grabbing.")

        # Release resources
        self.streamSource.contents.release(self.streamSource)
        self.streamSource = None

    def get_frame(self):
        if self.g_isStop:
            raise ValueError("Grabbing has been stopped.")

        frame = self.streamSource.contents.getFrame(self.streamSource, c_int(200))
        if frame.contents.valid(frame) != 0:
            raise ValueError("Invalid frame.")

        imageParams = IMGCNV_SOpenParam()
        imageParams.dataSize = frame.contents.getImageSize(frame)
        imageParams.height = frame.contents.getImageHeight(frame)
        imageParams.width = frame.contents.getImageWidth(frame)
        imageParams.paddingX = frame.contents.getImagePaddingX(frame)
        imageParams.paddingY = frame.contents.getImagePaddingY(frame)
        imageParams.pixelForamt = frame.contents.getImagePixelFormat(frame)

        imageBuff = frame.contents.getImage(frame)
        userBuff = c_buffer(b"\0", imageParams.dataSize)
        memmove(userBuff, c_char_p(imageBuff), imageParams.dataSize)

        frame.contents.release(frame)

        if imageParams.pixelForamt == EPixelType.gvspPixelMono8:
            grayByteArray = bytearray(userBuff)
            cvImage = numpy.array(grayByteArray).reshape(
                imageParams.height, imageParams.width
            )
        else:
            rgbSize = c_int()
            rgbBuff = c_buffer(b"\0", imageParams.height * imageParams.width * 3)

            nRet = IMGCNV_ConvertToBGR24(
                cast(userBuff, c_void_p),
                byref(imageParams),
                cast(rgbBuff, c_void_p),
                byref(rgbSize),
            )

            colorByteArray = bytearray(rgbBuff)
            cvImage = numpy.array(colorByteArray).reshape(
                imageParams.height, imageParams.width, 3
            )

        return cvImage

    def on_get_frame(self, frame, userInfo):
        if self.g_isStop:
            return

        nRet = frame.contents.valid(frame)
        if nRet != 0:
            print("Frame is invalid!")
            frame.contents.release(frame)
            return

        imageParams = IMGCNV_SOpenParam()
        imageParams.dataSize = frame.contents.getImageSize(frame)
        imageParams.height = frame.contents.getImageHeight(frame)
        imageParams.width = frame.contents.getImageWidth(frame)
        imageParams.paddingX = frame.contents.getImagePaddingX(frame)
        imageParams.paddingY = frame.contents.getImagePaddingY(frame)
        imageParams.pixelForamt = frame.contents.getImagePixelFormat(frame)

        imageBuff = frame.contents.getImage(frame)
        userBuff = c_buffer(b"\0", imageParams.dataSize)
        memmove(userBuff, c_char_p(imageBuff), imageParams.dataSize)

        frame.contents.release(frame)

        if imageParams.pixelForamt == EPixelType.gvspPixelMono8:
            grayByteArray = bytearray(userBuff)
            cvImage = numpy.array(grayByteArray).reshape(
                imageParams.height, imageParams.width
            )
        else:
            rgbSize = c_int()
            rgbBuff = c_buffer(b"\0", imageParams.height * imageParams.width * 1)

            nRet = IMGCNV_ConvertToMono8(
                cast(userBuff, c_void_p),
                byref(imageParams),
                cast(rgbBuff, c_void_p),
                byref(rgbSize),
            )

            colorByteArray = bytearray(rgbBuff)
            cvImage = numpy.array(colorByteArray).reshape(
                imageParams.height, imageParams.width, 1
            )

        self.frame_queue.put(cvImage)
        gc.collect()

    def get_init_setup(self):
        param_list = {
            "gain": self.get_gain_value(),
            "gain_range": self.get_param_min_max("GainRaw"),
            "gain_increment": 1, # TODO
            "exposure": self.get_exposure_time(),
            "exposure_range": self.get_param_min_max("ExposureTime"),
            "exposure_increment": 1, # TODO
            "height_range": (1000, 1000),
            "width_range": (1000, 1000),
        }
        wx.PostEvent(self.event_catcher, CAMInit(param_list))
        return param_list

    def get_exposure_time(self):
        return self.get_param_value("ExposureTime")

    def set_exposure_time(self, exposure):
        self.set_param_value("ExposureTime", exposure)

    def get_gain_value(self):
        return self.get_param_value("GainRaw")

    def set_gain_value(self, gain):
        self.set_param_value("GainRaw", gain)

    def set_param_value(self, param=None, value=0):
        if param is None:
            raise ValueError("No param specified!")
        paramNode = pointer(GENICAM_DoubleNode())
        paramNodeInfo = GENICAM_DoubleNodeInfo()
        paramNodeInfo.pCamera = pointer(self.camera)
        paramNodeInfo.attrName = param.encode()
        nRet = GENICAM_createDoubleNode(byref(paramNodeInfo), byref(paramNode))
        if nRet != 0:
            raise ValueError("Failed to create {} Node.".format(param))

        nRet = paramNode.contents.setValue(paramNode, c_double(value))
        if nRet != 0:
            raise ValueError("Failed to set {} value.".format(param))

        paramNode.contents.release(paramNode)
        return 0

    def get_param_value(self, param=None):
        if param is None:
            raise ValueError("No param specified!")

        paramNode = pointer(GENICAM_DoubleNode())
        paramNodeInfo = GENICAM_DoubleNodeInfo()
        paramNodeInfo.pCamera = pointer(self.camera)
        paramNodeInfo.attrName = param.encode()
        nRet = GENICAM_createDoubleNode(byref(paramNodeInfo), byref(paramNode))
        if nRet != 0:
            raise ValueError("Failed to create {} Node.".format(param))

        param_val = pointer(c_double())
        nRet = paramNode.contents.getValue(paramNode, param_val)
        if nRet != 0:
            raise ValueError("Failed to get {}!".format(param))

        info = pointer(GENICAM_StreamStatisticsInfo())
        nRet = self.streamSource.contents.getStatisticsInfo(
            self.streamSource, byref(info)
        )
        print("Stream statistics: ", info.contents.u.U.fps)

        param_val = param_val.contents.value
        paramNode.contents.release(paramNode)
        return param_val

    def get_param_min_max(self, param=None):
        if param is None:
            raise ValueError("No param specified!")

        paramNode = pointer(GENICAM_DoubleNode())
        paramNodeInfo = GENICAM_DoubleNodeInfo()
        paramNodeInfo.pCamera = pointer(self.camera)
        paramNodeInfo.attrName = param.encode()
        nRet = GENICAM_createDoubleNode(byref(paramNodeInfo), byref(paramNode))
        if nRet != 0:
            raise ValueError("Failed to create {} Node.".format(param))

        param_min = pointer(c_double())
        nRet = paramNode.contents.getMinVal(paramNode, param_min)
        if nRet != 0:
            raise ValueError("Failed to get min value of {}!".format(param))
        param_min = param_min.contents.value

        param_max = pointer(c_double())
        nRet = paramNode.contents.getMaxVal(paramNode, param_max)
        if nRet != 0:
            raise ValueError("Failed to get max value of {}!".format(param))
        param_max = param_max.contents.value

        paramNode.contents.release(paramNode)
        return param_min, param_max

    def get_param_inc(self, param=None):
        if param is None:
            raise ValueError("No param specified!")

        paramNode = pointer(GENICAM_IntNode())
        paramNodeInfo = GENICAM_IntNodeInfo()
        paramNodeInfo.pCamera = pointer(self.camera)
        paramNodeInfo.attrName = param.encode()
        nRet = GENICAM_createDoubleNode(byref(paramNodeInfo), byref(paramNode))
        if nRet != 0:
            raise ValueError("Failed to create {} Node.".format(param))

        param_inc = pointer(c_longlong())
        nRet = paramNode.contents.getIncrement(paramNode, param_inc)
        if nRet != 0:
            raise ValueError("Failed to get increment of {}!".format(param))
        param_inc = param_inc.contents.value

        paramNode.contents.release(paramNode)
        return param_inc

    def get_usb_info(self, param=None):
        paramNode = pointer(GENICAM_UsbCamera())
        paramNodeInfo = GENICAM_UsbCameraInfo()
        paramNodeInfo.pCamera = pointer(self.camera)
        paramNodeInfo.attrName = b"isHighSpeedSupported"
        nRet = GENICAM_createUsbCamera(byref(paramNodeInfo), byref(paramNode))
        if nRet != 0:
            raise ValueError("Failed to create {} Node.".format(param))

        print(
            "Is Hight speed supported? ",
            paramNode.contents.isLowSpeedSupported(paramNode),
        )

    def subscribe_camera_status(self):
        self.connect_callback_func = connectCallBackEx(self.device_link_notify)
        eventSubscribe = pointer(GENICAM_EventSubscribe())
        eventSubscribeInfo = GENICAM_EventSubscribeInfo()
        eventSubscribeInfo.pCamera = pointer(self.camera)
        nRet = GENICAM_createEventSubscribe(
            byref(eventSubscribeInfo), byref(eventSubscribe)
        )
        if nRet != 0:
            print("create eventSubscribe fail!")
            return -1

        nRet = eventSubscribe.contents.subscribeConnectArgsEx(
            eventSubscribe, self.connect_callback_func, g_cameraStatusUserInfo
        )
        if nRet != 0:
            print("subscribeConnectArgsEx fail!")
            eventSubscribe.contents.release(eventSubscribe)
            return -1

        eventSubscribe.contents.release(eventSubscribe)
        print("Subscribed!")
        return 0

    def unsubscribe_camera_status(self):
        eventSubscribe = pointer(GENICAM_EventSubscribe())
        eventSubscribeInfo = GENICAM_EventSubscribeInfo()
        eventSubscribeInfo.pCamera = pointer(self.camera)
        nRet = GENICAM_createEventSubscribe(
            byref(eventSubscribeInfo), byref(eventSubscribe)
        )
        if nRet != 0:
            print("create eventSubscribe fail!")
            return -1

        nRet = eventSubscribe.contents.unsubscribeConnectArgsEx(
            eventSubscribe, self.connect_callback_func, g_cameraStatusUserInfo
        )
        if nRet != 0:
            print("unsubscribeConnectArgsEx fail!")
            eventSubscribe.contents.release(eventSubscribe)
            return -1

        eventSubscribe.contents.release(eventSubscribe)
        print("Unsubscribed!")
        return 0

    def trigger_off(self):
        """Turns the trigger mode off"""
        trigModeEnumNode = pointer(GENICAM_EnumNode())
        trigModeEnumNodeInfo = GENICAM_EnumNodeInfo()
        trigModeEnumNodeInfo.pCamera = pointer(self.camera)
        trigModeEnumNodeInfo.attrName = b"TriggerMode"
        nRet = GENICAM_createEnumNode(
            byref(trigModeEnumNodeInfo), byref(trigModeEnumNode)
        )
        if nRet != 0:
            print("create TriggerMode Node fail!")
            self.streamSource.contents.release(self.streamSource)
            return -1

        nRet = trigModeEnumNode.contents.setValueBySymbol(trigModeEnumNode, b"Off")
        if nRet != 0:
            print("set TriggerMode value [Off] fail!")
            trigModeEnumNode.contents.release(trigModeEnumNode)
            self.streamSource.contents.release(self.streamSource)
            return -1

        trigModeEnumNode.contents.release(trigModeEnumNode)

        print("Trigger turned off!")

    def device_link_notify(self, connectArg, linkInfo):
        if EVType.offLine == connectArg.contents.m_event:
            print("camera has off line, userInfo [%s]" % (c_char_p(linkInfo).value))
        elif EVType.onLine == connectArg.contents.m_event:
            print("camera has on line, userInfo [%s]" % (c_char_p(linkInfo).value))

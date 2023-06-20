import wx
import wx.lib.newevent

EVT_ON_CROP = wx.NewId()

EVT_ENOUGH_POINTS = wx.NewId()
EVT_NOT_ENOUGH_POINTS = wx.NewId()

EVT_UPDT_CAM = wx.NewId()

EVT_CALIBRATION = wx.NewId()

EVT_LENS_CALIBRATION = wx.NewId()
EVT_LENS_CALIBRATION_INIT = wx.NewId()
EVT_LENS_CALIBRATION_STOP = wx.NewId()

EVT_MAX_FRAME_INTEN = wx.NewId()

EVT_PASS_FPS = wx.NewId()

EVT_BEAM_CENTERS = wx.NewId()

## Camera events
EVT_CAM_INIT = wx.NewId()
EVT_CAM_IMG = wx.NewId()
EVT_CAM_PARAM = wx.NewId()

## Update mouse XY
EVT_MOUSE_XY = wx.NewId()

class MouseXY(wx.PyEvent):
    def __init__(self, x, y):
        wx.PyEvent.__init__(self)
        self.x = x
        self.y = y
        self.SetEventType(EVT_MOUSE_XY)


class CAMInit(wx.PyEvent):
    def __init__(self, prop):
        wx.PyEvent.__init__(self)
        self.prop = prop
        self.SetEventType(EVT_CAM_INIT)


class CAMImage(wx.PyEvent):
    def __init__(self, img, beam_centers=[]):
        wx.PyEvent.__init__(self)
        self.img = img
        self.beam_centers = beam_centers
        self.SetEventType(EVT_CAM_IMG)


class CAMParam(wx.PyEvent):
    def __init__(self, param: str, val):
        wx.PyEvent.__init__(self)
        self.param = param
        self.val = val
        self.SetEventType(EVT_CAM_PARAM)


class PassFPS(wx.PyEvent):
    def __init__(self, array):
        wx.PyEvent.__init__(self)
        self.fps = array
        self.SetEventType(EVT_PASS_FPS)


class UpdateIntensity(wx.PyEvent):
    def __init__(self, array):
        wx.PyEvent.__init__(self)
        self.intensity = array
        self.SetEventType(EVT_MAX_FRAME_INTEN)


class CropEvent(wx.PyEvent):
    def __init__(self, array):
        wx.PyEvent.__init__(self)
        self.array = array
        self.SetEventType(EVT_ON_CROP)


class EnoughPoints(wx.PyEvent):
    def __init__(self, array):
        wx.PyEvent.__init__(self)
        self.values = array
        self.SetEventType(EVT_ENOUGH_POINTS)


class NotEnoughPoints(wx.PyEvent):
    def __init__(self, array):
        wx.PyEvent.__init__(self)
        self.values = array
        self.SetEventType(EVT_NOT_ENOUGH_POINTS)


class UpdateCamera(wx.PyEvent):
    def __init__(self, array, res):
        wx.PyEvent.__init__(self)
        self.value = array
        self.res = res
        self.SetEventType(EVT_UPDT_CAM)


class OnCalibration(wx.PyEvent):
    def __init__(self, array):
        wx.PyEvent.__init__(self)
        self.value = array
        self.SetEventType(EVT_CALIBRATION)


class OnLensCalibration(wx.PyEvent):
    def __init__(self, array):
        wx.PyEvent.__init__(self)
        self.value = array
        self.SetEventType(EVT_LENS_CALIBRATION)


class OnLensCalibrationInit(wx.PyEvent):
    def __init__(self, array):
        wx.PyEvent.__init__(self)
        self.value = array
        self.SetEventType(EVT_LENS_CALIBRATION_INIT)


class OnLensCalibrationStop(wx.PyEvent):
    def __init__(self, array):
        wx.PyEvent.__init__(self)
        self.value = array
        self.SetEventType(EVT_LENS_CALIBRATION_STOP)


class OnBeamCenters(wx.PyEvent):
    def __init__(self, array):
        wx.PyEvent.__init__(self)
        self.centers = array
        self.SetEventType(EVT_BEAM_CENTERS)

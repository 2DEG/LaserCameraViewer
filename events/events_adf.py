import wx
import  wx.lib.newevent

EVT_ON_CROP = wx.NewId()

EVT_ENOUGH_POINTS = wx.NewId()
EVT_NOT_ENOUGH_POINTS = wx.NewId()

EVT_UPDT_CAM = wx.NewId()

EVT_CALIBRATION = wx.NewId()

EVT_LENS_CALIBRATION = wx.NewId()
EVT_LENS_CALIBRATION_INIT = wx.NewId()
EVT_LENS_CALIBRATION_STOP = wx.NewId()
EVT_ON_SCREENSHOT = wx.NewId()

## ADF Camera events
EVT_ADF_IMG = wx.NewId()
EVT_ADF_EXPO = wx.NewId()
EVT_ADF_TEMP_TINT = wx.NewId()
EVT_ADF_STILL_IMG = wx.NewId()
EVT_ADF_ERROR = wx.NewId()

class ADFImage(wx.PyEvent):
	def __init__(self, img):
		wx.PyEvent.__init__(self)
		self.img = img
		self.SetEventType(EVT_ADF_IMG)

class ADFExposure(wx.PyEvent):
	def __init__(self, expo, gain):
		wx.PyEvent.__init__(self)
		self.exp = expo
		self.gain = gain
		self.SetEventType(EVT_ADF_EXPO)

class ADFTempTint(wx.PyEvent):	
	def __init__(self, temp, tint):
		wx.PyEvent.__init__(self)
		self.temp = temp
		self.tint = tint
		self.SetEventType(EVT_ADF_TEMP_TINT)

class ADFStillImage(wx.PyEvent):
	def __init__(self, img):
		wx.PyEvent.__init__(self)
		self.img = img
		self.SetEventType(EVT_ADF_STILL_IMG)
## -------------------

class CropEvent(wx.PyEvent):
	def __init__(self, array):
		wx.PyEvent.__init__(self)
		self.array = array
		self.SetEventType(EVT_ON_CROP)

class ScreenshotEvent(wx.PyEvent):
	def __init__(self, array):
		wx.PyEvent.__init__(self)
		self.array = array
		self.SetEventType(EVT_ON_SCREENSHOT)

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
	def __init__(self, array, res, is_settings = False):
		wx.PyEvent.__init__(self)
		self.value = array
		self.res = res
		self.is_settings = is_settings
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
        


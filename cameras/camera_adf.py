import wx
import ADF_SDK.adfcam as adfcam
from events.events_adf import ADFExposure, ADFImage, ADFStillImage, ADFTempTint
from cameras.camera_abc import *
import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)

import threading

class Camera_ADF(Camera_ABC, threading.Thread):

	def __init__(self, *args, event_catcher=None, frame_queue=None, **kw):
		threading.Thread.__init__(self)
		self.cur_cam = None
		self.event_catcher = event_catcher
		self.frame_queue = frame_queue
		
		if self.cur_cam is None: 
			arr = adfcam.Adfcam.EnumV2()
			# print(arr)
			if 0 == len(arr):
				logger.warning("No camera found.")
			else:
				self.cur_cam = arr[0]
				# print("Self.cur_cam: ", self.cur_cam)
				logger.info("Camera found: {}".format(self.cur_cam))

		self.hcam = None
		# self.timer = QTimer(self)
		self.imgWidth = 0
		self.imgHeight = 0
		self.pData = None
		self.res = 0
		self.temp = adfcam.ADFCAM_TEMP_DEF
		self.tint = adfcam.ADFCAM_TINT_DEF
		self.count = 0

	def is_connected(self):
		if self.cur_cam is None:
			return False
		return True

	def stop(self):
		self.close_camera()
		if self.isAlive():
			self.join()

	def join(self, timeout=None):
		# self.stop()
		super().join(timeout)

	def run(self):
		self.open_camera()
		
	
	def open_camera(self):
		if self.cur_cam is None:
			logger.error("Can not open the camera.")
			return False
		else:
			self.hcam = adfcam.Adfcam.Open(self.cur_cam.id)
			logger.info("Camera opened: {}".format(self.cur_cam))

		if self.hcam:
			self.res = self.hcam.get_eSize()
			self.imgWidth = self.cur_cam.model.res[self.res].width
			self.imgHeight = self.cur_cam.model.res[self.res].height
			self.hcam.put_Option(adfcam.ADFCAM_OPTION_BYTEORDER, 0) #Qimage use RGB byte order
	
			self.bit_depth_regime = 8

			if  int(self.hcam.MaxBitDepth()) > 8:
				self.bit_depth_regime = 16

			self.hcam.put_AutoExpoEnable(0)
			self.start_camera()
		
		return True

	def start_camera(self):
		if self.bit_depth_regime == 8:
			self.pData = bytes(adfcam.TDIBWIDTHBYTES(self.imgWidth * 8) * self.imgHeight)
		else:
			self.pData = bytes(adfcam.TDIBWIDTHBYTES(self.imgWidth * 16) * self.imgHeight)

		try:
			self.hcam.StartPullModeWithCallback(self.event_callback, self)
		except adfcam.HRESULTException:
			self.close_camera()

	def close_camera(self):
		if self.hcam:
			self.hcam.Close()
		self.hcam = None
		self.pData = None

	def get_resolutions_list(self):
		arr = []
		for i in range(0, self.cur_cam.model.preview):
			arr.append([self.cur_cam.model.res[i].width, self.cur_cam.model.res[i].height])
		
		return arr

	def set_resolution(self, index):
		if self.hcam: #step 1: stop camera
			self.hcam.Stop()

		self.res = index
		self.imgWidth = self.cur_cam.model.res[index].width
		self.imgHeight = self.cur_cam.model.res[index].height

		if self.hcam: #step 2: restart camera
			self.hcam.put_eSize(self.res)
			self.start_camera()
	
	def set_exposure(self, exposure):
		if self.hcam:
			self.hcam.put_ExpoTime(exposure)

	def set_auto_exposure(self, auto = True):
		if self.hcam:
			if auto:
				self.hcam.put_AutoExpoEnable(1)
			else:
				self.hcam.put_AutoExpoEnable(0)
	
	def set_gain(self, gain):
		if self.hcam:
			self.hcam.put_ExpoAGain(gain)

	def get_exposure(self):
		if self.hcam:
			return self.hcam.get_ExpoTime()
		
	def get_gain(self):
		if self.hcam:
			return self.hcam.get_ExpoAGain()
		
	def get_exposure_range(self):
		if self.hcam:
			return self.hcam.get_ExpTimeRange()
	
	def get_gain_range(self):
		if self.hcam:
			return self.hcam.get_ExpoAGainRange()
		
	def grab_frame(self):
		pass

	def get_cam_id(self):
		pass

	def enum_cameras(self):
		arr = adfcam.Adfcam.EnumV2()
		return len(arr), arr 
		
	
	@staticmethod
	def event_callback(nEvent, self):
		'''callbacks come from adfcam.dll/so internal threads, so we use qt signal to post this event to the UI thread'''
		# self.evtCallback.emit(nEvent)
		# print("Get events: ", nEvent)
		if adfcam.ADFCAM_EVENT_IMAGE == nEvent:
			# print("Here should be frames!")
			self.handle_img_event()
		elif adfcam.ADFCAM_EVENT_EXPOSURE == nEvent:
			self.handle_exp_event()
		elif adfcam.ADFCAM_EVENT_TEMPTINT == nEvent:
			self.handle_temp_tint_event()
		# elif adfcam.ADFCAM_EVENT_STILLIMAGE == nEvent:
		# 	self.handleStillImageEvent()
		elif adfcam.ADFCAM_EVENT_ERROR == nEvent:
			self.close_camera()
			logger.warning("Camera generic error.")
		elif adfcam.ADFCAM_EVENT_STILLIMAGE == nEvent:
			self.close_camera()
			logger.warning("Camera still image.")
			# print("Warning", "Camera disconnect.")

	def handle_img_event(self):
		# print("Inside image handler")
		if self.event_catcher and self.hcam:
			
			try:
				self.hcam.PullImageV3(self.pData, 0, self.bit_depth_regime, 0, None)
				# print("Catch a frame!")
			except adfcam.HRESULTException:
				logger.warning("Unsupported color depth bits.")
				# print("Unsupported color depth bits")
				pass

			if self.bit_depth_regime == 8:
				img = np.frombuffer(self.pData, dtype=np.uint8).reshape(self.imgHeight, self.imgWidth)
				# image = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
			else:
				image_array = np.frombuffer(self.pData, dtype=np.uint16).reshape(self.imgHeight, self.imgWidth)
				img = (image_array/256).astype('uint8')
				# image = cv2.cvtColor(img8, cv2.COLOR_GRAY2RGB)
			image = img
			# wx.PostEvent(self.event_catcher, ADFImage(image))
			self.frame_queue.put(image)

	def handle_exp_event(self):
		if self.event_catcher and self.hcam:
			try:
				exp = self.hcam.get_ExpTimeRange()
				exp = (self.hcam.get_ExpoTime(), ) + exp
				gain = self.hcam.get_ExpoAGainRange()
				gain = (self.hcam.get_ExpoAGain(), ) + gain
			except adfcam.HRESULTException:
				pass
			wx.PostEvent(self.event_catcher, ADFExposure(exp, gain))

	def handle_temp_tint_event(self):
		if self.event_catcher and self.hcam:
			try:
				n_temp, n_tint = self.hcam.get_TempTint()
			except adfcam.HRESULTException:
				pass
			wx.PostEvent(self.event_catcher, ADFTempTint(n_temp, n_tint))
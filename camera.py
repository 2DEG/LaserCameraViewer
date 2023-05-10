from builtins import range
from builtins import object
import cv2
import time


class Camera(object):

	def __init__(self, camera_id=0, is_colored=False):
		self.camera_id = camera_id
		self._capture = None
		self._is_connected = False
		self.is_colored = is_colored

		self.connect()

	def connect(self):
		self._is_connected = False
		self._capture = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
		# self._capture.set(cv2.CAP_PROP_SETTINGS, 1)
		print(self._capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3))
		print(self._capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)) # manual mode
		print(self._capture.set(cv2.CAP_PROP_EXPOSURE, -1))
		time.sleep(0.2)
		if self._capture.isOpened():
			self._is_connected = True

	def disconnect(self):
		if self._is_connected:
			if self._capture is not None:
				if self._capture.isOpened():
					self._is_connected = False
					self._capture.release()

	def capture_image(self, flush=0, mirror=False):
		if self._is_connected:
			if flush > 0:
				for i in range(0, flush):
					self._capture.grab()
			ret, image = self._capture.read()
			# print(image.shape)
			if ret:
				# image = cv2.transpose(image)
				if not mirror:
					image = cv2.flip(image, 0)
				# print("Original Image:", image)
				if self.is_colored:
					image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
				else:
					image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
					image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB) # Kek
				# print("Grey_scale Image:", image)
				return image

	def set_resolution(self, height, width):
		if self._is_connected:
			self._set_width(width)
			self._set_height(height)
			self._update_resolution()

	def _set_width(self, value):
		self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, value)

	def _set_height(self, value):
		self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, value)

	def get_resolution(self):
		if self._is_connected:
			return self._get_width(), self._get_height()

	def _get_width(self):
		return self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)

	def _get_height(self):
		return self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)


	def _update_resolution(self):
		self._width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
		self._height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
from collections.abc import Callable, Iterable, Mapping
import sys
import threading
import copy
import queue
from time import sleep
import numpy
from typing import Any, Optional
from abc import ABC, abstractmethod
import wx 
from events import CAMImage, CAMParam


import cv2

from vmbpy import *

# All frames will either be recorded in this format, or transformed to it before being displayed
opencv_display_format = PixelFormat.Mono8

FRAME_HEIGHT = 1080
FRAME_WIDTH = 1080


def resize_if_required(frame: Frame) -> numpy.ndarray:
	# Helper function resizing the given frame, if it has not the required dimensions.
	# On resizing, the image data is copied and resized, the image inside the frame object
	# is untouched.
	cv_frame = frame.as_opencv_image()

	if (frame.get_height() != FRAME_HEIGHT) or (frame.get_width() != FRAME_WIDTH):
		cv_frame = cv2.resize(
			cv_frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA
		)
		cv_frame = cv_frame[..., numpy.newaxis]

	return cv_frame


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
		print("Camera {}: Failed to get value of Feature '{}'".format(cam.get_id(), feat_name))

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


def try_put_frame(q: queue.Queue, cam: Camera, frame: Optional[Frame]):
	try:
		q.put_nowait((cam.get_id(), frame))

	except queue.Full:
		pass

def inheritors(klass):
	return {child.__name__: child for child in klass.__subclasses__()}


## Abstract camera class
class Camera(ABC):
	def __init__(self, *args, **kwargs):
		super().__init__()

	def __new__(cls, backend):
		subclasses = inheritors(cls)
		if not backend in subclasses.keys():
			raise ValueError("Invalid backend '{}'".format(backend))
		subclass = subclasses[backend]
		instance = super(Camera, subclass).__new__(subclass)
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


class Camera_AV(Camera,  threading.Thread):
	"""Class for Allied Vision cameras"""

	def __init__(self, *args, event_catcher= None, **kw):
		threading.Thread.__init__(self)
		self.command_queue = queue.Queue()
		self.producer = None
		self.event_catcher = event_catcher

		try:
			with VmbSystem.get_instance() as vmb:
				for cam in vmb.get_all_cameras():
					print(cam.get_id() == "DEV_1AB22C01054E")
					with cam:
						self.param_list = {
							"gain_range": cam.Gain.get_range(),
							"gain_increment": cam.Gain.get_increment(),
							"exposure_range": cam.ExposureTime.get_range(),
							"exposure_increment": cam.ExposureTime.get_increment(),
						}
		except VmbCameraError:
			pass

	class Producer(threading.Thread):
		def __init__(self, command_queue, event_catcher=None):
			threading.Thread.__init__(self)
			self.killswitch = threading.Event()
			self.event_catcher = event_catcher
			self.command_queue = command_queue

		def __call__(self, cam: Camera, stream: Stream, frame: Frame):
			
			# This method is executed within VmbC context. All incoming frames
			# are reused for later frame acquisition. If a frame shall be queued, the
			# frame must be copied and the copy must be sent, otherwise the acquired
			# frame will be overridden as soon as the frame is reused.
			if frame.get_status() == FrameStatus.Complete:
				wx.PostEvent(self.event_catcher, CAMImage(frame))
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
										command, value = self.command_queue.get(timeout=0.1) # One may use get_nowait() instead, but it is too fast, so one should handle queue.Empty
									except queue.Empty:
										continue
									else:
										if value is not None:
											set_nearest_value(cam, command, value)
										else:
											val = get_value(cam, command)
											if val:
												wx.PostEvent(self.event_catcher, CAMParam(command, val))

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
		self.producer = self.Producer(self.command_queue, self.event_catcher)
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
		# return self.get_param("exposure")
		return 200

	def get_gain(self):
		self.command_queue.put(("Gain", None))
		# return self.get_param("gain")
		return 1

	def grab_frame(self, n=1):
		pass

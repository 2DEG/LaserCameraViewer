from collections.abc import Callable, Iterable, Mapping
import sys
import threading
import copy
import queue
from time import sleep
import numpy
from typing import Any, Optional
from abc import ABC, abstractmethod


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


# def create_dummy_frame() -> numpy.ndarray:
#     cv_frame = numpy.zeros((50, 640, 1), numpy.uint8)
#     cv_frame[:] = 0

#     cv2.putText(
#         cv_frame,
#         "No Stream available. Please connect a Camera.",
#         org=(30, 30),
#         fontScale=1,
#         color=255,
#         thickness=1,
#         fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,
#     )

#     return cv_frame


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


class Camera_AV(Camera, threading.Thread):
	"""Class for Allied Vision cameras"""

	def __init__(self, *args, **kw):
		threading.Thread.__init__(self)
		self.cam_queue = queue.Queue()
		self.stop_cam_evt = threading.Event()
		self.producer = None

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
		def __init__(self, frame_queue: queue.Queue):
			threading.Thread.__init__(self)
			self.frame_queue = frame_queue
			self.killswitch = threading.Event()

		def __call__(self, cam: Camera, stream: Stream, frame: Frame):
			# This method is executed within VmbC context. All incoming frames
			# are reused for later frame acquisition. If a frame shall be queued, the
			# frame must be copied and the copy must be sent, otherwise the acquired
			# frame will be overridden as soon as the frame is reused.
			if frame.get_status() == FrameStatus.Complete:
				# print("Before set")
				if not self.frame_queue.full():
					frame_cpy = copy.deepcopy(frame)
					try_put_frame(self.frame_queue, cam, frame_cpy)

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
								self.killswitch.wait()

							finally:
								cam.stop_streaming()
								print("Streaming stopped")

							print("Streaming ended")
			except VmbCameraError:
				pass

	def stop(self):
		self.producer.stop()
		if self.isAlive():
			self.stop_cam_evt.set()
			self.join()

	def run(self):
		self.producer = self.Producer(self.cam_queue)
		print("Here")
		self.producer.start()
		print("After producer")

	def get_cam_id(self):
		pass

	def set_exposure(self, exposure):
		return self.set_param("exposure", exposure)

	def set_gain(self, gain):
		return self.set_param("gain", gain)

	def set_param(self, param="", val=0):
		alive = True
		real = 0
		if self.producer is not None and self.producer.isAlive():
			self.producer.stop()
			alive = False

		try:
			with VmbSystem.get_instance() as vmb:
				for cam in vmb.get_all_cameras():
					print(cam.get_id() == "DEV_1AB22C01054E")
					with cam:
						if param == "exposure":
							try:
								print(
									"Exposure before setting: ", cam.ExposureTime.get()
								)
								cam.ExposureTime.set(val)
							except (AttributeError, VmbFeatureError):
								pass

							try:
								real = cam.ExposureTime.get()
								print("Exposure after setting: ", real)
							except (AttributeError, VmbFeatureError):
								pass

						elif param == "gain":
							try:
								print("Gain before setting: ", cam.Gain.get())
								cam.Gain.set(val)
							except (AttributeError, VmbFeatureError):
								pass

							try:
								real = cam.Gain.get()
								print("Gain after setting: ", real)
							except (AttributeError, VmbFeatureError):
								pass
		except VmbCameraError:
			pass

		if not alive:
			self.producer.run()

		return real

	def get_exposure(self):
		return self.get_param("exposure")

	def get_gain(self):
		return self.get_param("gain")

	def get_param(self, param=""):
		alive = True
		if self.producer is not None and self.producer.isAlive():
			self.producer.stop()
			alive = False

		try:
			with VmbSystem.get_instance() as vmb:
				for cam in vmb.get_all_cameras():
					print(cam.get_id() == "DEV_1AB22C01054E")
					with cam:
						try:
							if param == "exposure":
								res = cam.ExposureTime.get()
							elif param == "gain":
								res = cam.Gain.get()
						except (AttributeError, VmbFeatureError):
							pass
		except VmbCameraError:
			pass

		if not alive:
			self.producer.run()

		return res

	def grab_frame(self, n=1):
		frames = []

		with self.cam_queue.mutex:
			self.cam_queue.queue.clear()
		while len(frames) != n:
			# print("Me")
			frames_left = self.cam_queue.qsize()
			# print(frames_left)

			while frames_left:
				try:
					_, frame = self.cam_queue.get_nowait()

				except queue.Empty:
					break

				# Add/Remove frame from current state.
				if frame:
					# frame = frame.convert_pixel_format(opencv_display_format).as_opencv_image()
					# print(frame)
					# frame = cv2.COLOR_GRAY2RGB(frame)
					frames.append(frame)

				else:
					frames.pop()

				frames_left -= 1
		return frames

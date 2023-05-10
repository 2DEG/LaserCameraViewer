import sys
import threading
import copy
import queue
from time import sleep
import numpy
from typing import Optional

import cv2

from vmbpy import *

# All frames will either be recorded in this format, or transformed to it before being displayed
opencv_display_format = PixelFormat.Mono8

FRAME_HEIGHT = 480
FRAME_WIDTH = 480

def resize_if_required(frame: Frame) -> numpy.ndarray:
	# Helper function resizing the given frame, if it has not the required dimensions.
	# On resizing, the image data is copied and resized, the image inside the frame object
	# is untouched.
	cv_frame = frame.as_opencv_image()

	if (frame.get_height() != FRAME_HEIGHT) or (frame.get_width() != FRAME_WIDTH):
		cv_frame = cv2.resize(cv_frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
		cv_frame = cv_frame[..., numpy.newaxis]

	return cv_frame


def create_dummy_frame() -> numpy.ndarray:
	cv_frame = numpy.zeros((50, 640, 1), numpy.uint8)
	cv_frame[:] = 0

	cv2.putText(cv_frame, 'No Stream available. Please connect a Camera.', org=(30, 30),
				fontScale=1, color=255, thickness=1, fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL)

	return cv_frame



def set_nearest_value(cam: Camera, feat_name: str, feat_value: int):
	# Helper function that tries to set a given value. If setting of the initial value failed
	# it calculates the nearest valid value and sets the result. This function is intended to
	# be used with Height and Width Features because not all Cameras allow the same values
	# for height and width.
	feat = cam.get_feature_by_name(feat_name)

	try:
		feat.set(feat_value)

	except VmbFeatureError:
		min_, max_ = feat.get_range()
		inc = feat.get_increment()

		if feat_value <= min_:
			val = min_

		elif feat_value >= max_:
			val = max_

		else:
			val = (((feat_value - min_) // inc) * inc) + min_

		feat.set(val)

		msg = ('Camera {}: Failed to set value of Feature \'{}\' to \'{}\': '
			   'Using nearest valid value \'{}\'. Note that, this causes resizing '
			   'during processing, reducing the frame rate.')
		Log.get_instance().info(msg.format(cam.get_id(), feat_name, feat_value, val))

def try_put_frame(q: queue.Queue, cam: Camera, frame: Optional[Frame]):
	try:
		q.put_nowait((cam.get_id(), frame))

	except queue.Full:
		pass

class Camera(threading.Thread):

	def __init__(self, callback = None) -> None:
		threading.Thread.__init__(self)
		self.cam_queue = queue.Queue()
		self.working_function = callback
		self.stop_cam_evt = threading.Event()
		
	
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
						with cam:
							set_nearest_value(cam, 'Height', FRAME_HEIGHT)
							set_nearest_value(cam, 'Width', FRAME_WIDTH)
							try:
								cam.ExposureAuto.set('Once')
							except (AttributeError, VmbFeatureError):
								pass

							try:
								cam.start_streaming(self)
								self.killswitch.wait()

							finally:
								cam.stop_streaming()
			except VmbCameraError:
				pass

	def stop(self):
		self.producer.stop()
		if self.isAlive():
			self.stop_cam_evt.set()
			self.join()
		# self.producer.join()

	def run(self):
		
		self.producer = self.Producer(self.cam_queue)
		print("Here")
		self.producer.start()
		print("After producer")
		# self.event = None
		# k = 0
		# alive = True

	def grab_frame(self, n = 1):
		frames = []
		# k = 0

		if self.working_function is not None:
			# print("Inside loop")
			with self.cam_queue.mutex:
				self.cam_queue.queue.clear()
			while len(frames) != n:
				# print("Me")
				frames_left = self.cam_queue.qsize()
				# print(frames_left)
				
				while frames_left:
					try:
						cam_id, frame = self.cam_queue.get_nowait()

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
				# k += 1
				# sleep(1/1000)
				# if k == 10:
				# 	break
				# self.alive_cam.set()
				
		# self.event.clear()
		# self.alive_cam.clear()
		# print("Frames: ", frames)
		return frames

				# if frames:
				# 	cv_images = [frames[cam_id] for cam_id in sorted(frames.keys())]
				# 	self.working_function(cv_images)
				# k += 1
				# if k == 100:
				# 	self.alive_cam.set()
				



def main():
	camera = Camera(print)
	camera.start()
	sleep(1)
	print("First grab", camera.grab_frame())
	sleep(1)
	print("Second grab", camera.grab_frame())
	sleep(1)
	camera.stop()
	camera.join()


# if __name__ == '__main__':
# 	main()

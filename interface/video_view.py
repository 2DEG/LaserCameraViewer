import wx
import cv2
import os
import csv

from PIL import Image
from datetime import datetime


from vmbpy import *

import threading
import queue

from interface.image_view import ImageView
from events.events import (
    UpdateIntensity,
    OnBeamCenters,
    MouseXY,
    CAMImage,
)

class Frame_Processor(threading.Thread):
    def __init__(self, frame_queue, event_catcher=None):
            threading.Thread.__init__(self)
            self.killswitch = threading.Event()
            self.event_catcher = event_catcher
            self.frame_queue = frame_queue
    
    def stop(self):
            if self.isAlive():
                self.killswitch.set()
                self.join()

    def run(self):
        while not self.killswitch.is_set():
            try:
                frame = self.frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            else:
                if frame is not None:
                    # print("Frame max:", frame.max())
                    wx.PostEvent(self.event_catcher, UpdateIntensity(frame.max()))
                    frame, ellipse_centers = detect_ellipses(frame)
                    if len(ellipse_centers) != 0:
                        wx.PostEvent(self.event_catcher, OnBeamCenters(ellipse_centers))
                
                    wx.PostEvent(self.event_catcher, CAMImage(frame, ellipse_centers))
        print("Frame processing ended")

class VideoView(ImageView):
    """
    A class used to represent a video view.
    Inherits from ImageView class.
    """

    def __init__(self, *args, **kw):
        ImageView.__init__(self, *args, **kw)

        self.meas_on = False
        self.run_meas = False

        self.startPos = None
        self.recentPos = None
        self.start_line = False

        self.draw_rect = False
        self.rect_crop = False
        self.rect_end = None
        self.zoom_pipeline = []
        self.rect_start = None

        self.cross_line_len = 100

        self.make_screen_shot = False
        self.rec_path = os.path.dirname(os.path.realpath(__file__))
        

        # Bind mouse events
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)
        self.Bind(wx.EVT_LEFT_UP, self.on_release)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_zoomout)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)

    def on_click(self, event):
        """
        Handles click event and captures mouse.

        Args:
            event: wxPython event.
        """

        self.CaptureMouse()
        self.rect_start = recalculate_coord(
            coord=event.GetPosition(),
            best_size=self.best_size,
            img_size=self.image_size,
        )

    def on_mouse_move(self, event):
        """
        Handles mouse move events. Sends updates on mouse position to the status bar.
        While dragging, draws a rectangle.

        Args:
            event: wxPython event.
        """

        x, y = recalculate_coord(
            coord=event.GetPosition(),
            best_size=self.best_size,
            img_size=self.image_size,
        )
        if event.Dragging() and event.LeftIsDown():
            self.draw_rect = True
            self.rect_end = [x, y]
            #
        wx.PostEvent(self, MouseXY(x, y))

    def on_release(self, event):
        """
        Handles mouse release events.
        Zooms in on the selected rectangle.

        Args:
            event: wxPython event.
        """

        if self.HasCapture():
            self.ReleaseMouse()
            self.draw_rect = False
            if self.rect_end is not None:
                if self.rect_end == self.rect_start:
                    self.rect_end = self.rect_start[0] + 1, self.rect_start[1] + 1
                self.zoom_pipeline.append([self.rect_start, self.rect_end])

    def on_zoomout(self, event):
        """
        Handles zoom out on a mouse left click.

        Args:
            event: wxPython event.
        """

        self.rect_end = None
        self.zoom_pipeline = []
        self.rect_start = None

    def make_screenshot(self, path):
        """
        Prepares for taking a screenshot.

        Args:
            path: Path to save the screenshot.
        """

        self.make_screen_shot = True
        self.rec_path = path

    def player(self, event):
        """
        Plays the video feed and handles related activities.
        Implemented as a callback function, which is called by camera thread when a new frame is available.

        Args:
            event: wxPython event.
        """

        frame = event.img
        self.ellipses_centers = event.beam_centers

        if frame is not None:

            if self.make_screen_shot:
                self.save_screenshot(frame)

            if self.zoom_pipeline != []:
                # if self.rect_start is not None and self.rect_end is not None:
                for each in self.zoom_pipeline:
                    # print(each)
                    frame = frame[
                        min(each[0][1], each[1][1]) : max(each[0][1], each[1][1]),
                        min(each[0][0], each[1][0]) : max(each[0][0], each[1][0]),
                    ]

            if self.draw_rect:
                # print("HI!")
                frame = self.draw_rectangle(frame)

            wx.CallAfter(self.set_frame, frame)

    def start(self):
        """
        Starts the video view.
        """

        pass

    def stop(self):
        """
        Stops the video view and sets the default image.
        """

        self.hide = True
        self.set_default_image()

    def draw_rectangle(self, frame):
        """
        Draws a rectangle on the given frame.

        Args:
            frame: A frame on which a rectangle will be drawn.
        """

        if self.rect_start is not None and self.rect_end is not None:
            return cv2.rectangle(
                frame,
                self.rect_start,
                self.rect_end,
                (255, 0, 0),
                thickness=2,
            )

    def save_screenshot(self, frame):
        """
        Saves a screenshot.

        Args:
            frame: Frame to be saved as screenshot.
        """

        if os.path.exists(self.rec_path):
            dt = datetime.now().strftime("%d%m%Y_%Hh%Mm%Ss")
            im = Image.fromarray(frame)
            im.save(os.path.join(self.rec_path, "{}.png".format(dt)))
        self.make_screen_shot = False

def recalculate_coord(coord, best_size, img_size):
    """
    Recalculates coordinates, taken from GUI panel into true coordinates of the frame.

    Args:
        coord: Original coordinates to be recalculated.
        best_size: Best size parameters.
        img_size: Image size parameters.
    """

    (circ_x, circ_y) = coord
    (i_w, i_h, x_of, y_of) = best_size
    (real_x, real_y) = img_size
    if x_of == 0:
        circ_y = circ_y - y_of
    if y_of == 0:
        circ_x = circ_x - x_of
    return int(circ_x * real_x / i_w), int(circ_y * real_y / i_h)


def detect_ellipses(gray, length=100):
    """
    Detects ellipses in an image.

    Args:
        img: Image to be processed.
        length: Length parameter for ellipse detection. Defaults to 100.
    """

    img = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)[1]

    # Dilate with elliptical shaped kernel
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilate = cv2.dilate(thresh, kernel, iterations=2)

    # Find contours, filter using contour threshold area, draw ellipse
    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # print(cnts)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    centers = []
    k = 0
    for c in cnts:
        if k > 5:
            break
        area = cv2.contourArea(c)
        if area > 50:
            try:
                ellipse = cv2.fitEllipse(c)
            except:
                continue
            a, b = ellipse[0]
            a = int(a)
            b = int(b)
            centers.append([a, b])
            delta = length
            cv2.line(img, (a - delta, b), (a + delta, b), (255, 0, 0), 1)
            cv2.line(img, (a, b - delta), (a, b + delta), (255, 0, 0), 1)
            cv2.ellipse(img, ellipse, (0, 255, 0), 2)
        k += 1

    return img, centers

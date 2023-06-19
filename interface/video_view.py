import wx
import cv2
import os
import csv

from PIL import Image
from datetime import datetime


from vmbpy import *


from interface.image_view import ImageView
from events.events import (
    EVT_LENS_CALIBRATION_INIT,
    EVT_LENS_CALIBRATION_STOP,
    CropEvent,
    OnLensCalibration,
    UpdateIntensity,
    OnBeamCenters,
)


class VideoView(ImageView):
    def __init__(self, *args, camera=None, **kw):
        ImageView.__init__(self, *args, **kw)

        self.meas_on = False
        self.run_meas = False

        self.draw_circ = False
        self.click = False
        self.radius = 30

        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)
        self.Bind(wx.EVT_LEFT_UP, self.on_release)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_zoomout)
        # self.Bind( wx.EVT_MOUSEWHEEL, self.on_wheel )
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)

        self.Connect(-1, -1, EVT_LENS_CALIBRATION_INIT, self.on_init_lens_cal)
        self.Connect(-1, -1, EVT_LENS_CALIBRATION_STOP, self.on_stop_lens_cal)

        self.startPos = None
        self.recentPos = None
        self.start_line = False
        self.is_lens_calibration = False

        self.draw_rect = False
        self.rect_crop = False
        self.rect_end = None
        self.zoom_pipeline = []
        self.rect_start = None

        self.collect_centers = False
        self.init_tracking = False
        self.tracking_arr = []

        self.cross_line_len = 100

        self.make_screen_shot = False
        self.rec_path = os.path.dirname(os.path.realpath(__file__))
        self.track_path = os.path.dirname(os.path.realpath(__file__))
        # self.overlay = wx.Overlay()

    def on_click(self, event):
        self.CaptureMouse()
        x, y  = event.GetPosition()
        self.rect_start = recalculate_coord(
            coord=[int(x), int(y)],
            best_size=self.get_best_size(),
            img_size=self.image.GetSize(),
        )

    def on_mouse_move(self, event):
        if event.Dragging() and event.LeftIsDown():
            self.draw_rect = True
            x, y  = event.GetPosition()
            self.rect_end = recalculate_coord(
                coord=[int(x), int(y)],
                best_size=self.get_best_size(),
                img_size=self.image.GetSize(),
            )

    def on_release(self, event):
        if self.HasCapture():
            self.ReleaseMouse()
            self.draw_rect = False
            if self.rect_end is not None:
                if self.rect_end == self.rect_start:
                    self.rect_end = self.rect_start[0] + 1, self.rect_start[1] + 1
                self.zoom_pipeline.append([self.rect_start, self.rect_end])

    def on_zoomout(self, event):
        # self.rect_crop = False
        self.rect_end = None
        self.zoom_pipeline = []
        self.rect_start = None

    def on_init_lens_cal(self, event):
        self.is_lens_calibration = True

    def on_stop_lens_cal(self, event):
        self.is_lens_calibration = False

    def on_wheel(self, event):
        if event.GetWheelRotation() < 0:
            self.radius += 5
        else:
            self.radius -= 5
            if self.radius < 5:
                self.radius = 5

    def make_screenshot(self, path):
        print("Make screent function entered!")
        self.make_screen_shot = True
        self.rec_path = path

    def player(self, event):
        frame = event.img
        # print("Frame: ", frame)

        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            wx.PostEvent(self, UpdateIntensity(frame.max()))

            if self.make_screen_shot:
                self.save_screenshot(frame)

            frame, ellipse_centers = detect_ellipses(frame, self.cross_line_len)
            # frame, ellipse_centers = frame, []

            if len(ellipse_centers) != 0:
                wx.PostEvent(self, OnBeamCenters(ellipse_centers))

            if self.init_tracking:
                if os.path.exists(self.track_path):
                    print("Tracking path is valid!")
                    dt = datetime.now().strftime("Track_%d%m%Y_%Hh%Mm%Ss")
                    self.tracking_file = os.path.join(
                        self.track_path, "{}.csv".format(dt)
                    )

                    self.update_tracking_data(ellipse_centers)
                self.init_tracking = False

            if self.collect_centers:
                self.update_tracking_data(ellipse_centers)
                self.collect_centers = False
                # self.init_tracking = False

            if self.zoom_pipeline != []:
                # if self.rect_start is not None and self.rect_end is not None:
                for each in self.zoom_pipeline:
                    # print(each)
                    frame = frame[
                        min(each[0][1], each[1][1]) : max(each[0][1], each[1][1]),
                        min(each[0][0], each[1][0]) : max(each[0][0], each[1][0]),
                    ]
                    # print(frame.shape)

            if self.draw_rect:
                # print("HI!")
                frame = self.draw_rectangle(frame)

            wx.CallAfter(self.set_frame, frame)

    def start(self):
        pass

    def stop(self):
        self.hide = True
        self.set_default_image()

    def update_tracking_data(self, data):
        self.tracking_arr.append(data)
        with open(self.tracking_file, "a") as my_csv:
            csvWriter = csv.writer(my_csv, delimiter=",")
            csvWriter.writerows(data)

    def draw_rectangle(self, frame):
        if self.rect_start is not None and self.rect_end is not None:
            return cv2.rectangle(
                frame,
                self.rect_start,
                self.rect_end,
                (255, 0, 0),
                thickness=2,
            )

    def save_screenshot(self, frame):
        if os.path.exists(self.rec_path):
            dt = datetime.now().strftime("%d%m%Y_%Hh%Mm%Ss")
            im = Image.fromarray(frame)
            im.save(os.path.join(self.rec_path, "{}.png".format(dt)))
        self.make_screen_shot = False

def recalculate_coord(coord, best_size, img_size):
    (circ_x, circ_y) = coord
    (i_w, i_h, x_of, y_of) = best_size
    (real_x, real_y) = img_size
    if x_of == 0:
        circ_y = circ_y - y_of
    if y_of == 0:
        circ_x = circ_x - x_of
    return int(circ_x * real_x / i_w), int(circ_y * real_y / i_h)


def detect_ellipses(img, length=100):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)[1]

    # Dilate with elliptical shaped kernel
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilate = cv2.dilate(thresh, kernel, iterations=2)

    # Find contours, filter using contour threshold area, draw ellipse
    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # print(cnts)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    centers = []

    for c in cnts:
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

    return img, centers

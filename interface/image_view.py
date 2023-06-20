import wx
import time
import cv2

from events.events import PassFPS

WIDTH = 640
HEIGHT = 480


class ImageView(wx.Panel):
    def __init__(
        self,
        parent,
        resize=True,
        quality=wx.IMAGE_QUALITY_NORMAL,
        size=(-1, -1),
        black=False,
        style=wx.NO_BORDER,
    ):
        wx.Panel.__init__(self, parent, size=size, style=style)

        self.x_offset = 0
        self.y_offset = 0
        self.quality = quality
        self.fps = 0
        self.time_start = time.time()
        # self.dc = wx.BufferedPaintDC(self)

        self.default_image = wx.Image(WIDTH, HEIGHT, clear=True)
        self.image = self.default_image
        self.image_size = self.image.GetSize()
        self.best_size = self.get_best_size()
        # self.bitmap = wx.BitmapFromImage(self.default_image)
        self.bitmap = wx.Bitmap(self.default_image)

        if black:
            self.SetBackgroundColour(wx.BLACK)

        self.backBrush = wx.Brush(wx.BLACK, wx.SOLID)

        self.SetDoubleBuffered(True)  # This is the key to stop flicker (!!!)

        self.Bind(wx.EVT_SHOW, self.on_show)
        self.Bind(wx.EVT_PAINT, self.on_paint)

        # self.timer = wx.Timer(self)
        # self.Bind(wx.EVT_TIMER, self.on_paint)

        if resize:
            self.Bind(wx.EVT_SIZE, self.on_resize)

        self.hide = False
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter)

    def on_enter(self, event):
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))

    def on_show(self, event):
        if event.IsShown():
            self.GetParent().Layout()
            self.Layout()

    def on_paint(self, event):
        if not self.hide:
            dc = wx.BufferedPaintDC(self)
            dc.SetBackground(self.backBrush)
            dc.Clear()
            dc.DrawBitmap(self.bitmap, self.x_offset, self.y_offset)

    def on_resize(self, size):
        self.refresh_bitmap()

    def set_image(self, image):
        if image is not None:
            if self.hide:
                self.hide = False
            self.image = image
            self.image_size = self.image.GetSize()
            self.refresh_bitmap()

    def set_default_image(self):
        self.set_image(self.default_image)

    def set_frame(self, frame):
        if frame is not None:
            self.fps += 1
            height, width = frame.shape[:2]
            # print(height, width)
            if time.time() - self.time_start >= 1:
                self.time_start = time.time()
                # print("FPS: {}".format(self.fps))
                wx.PostEvent(self, PassFPS(self.fps))
                self.fps = 0
            self.set_image(
                wx.ImageFromBuffer(width, height, cv2.resize(frame, (width, height)))
            )
            # self.set_image(wx.ConvertToGreyscale(width, height, frame))

    def refresh_bitmap(self):
        self.best_size = self.get_best_size()
        (w, h, self.x_offset, self.y_offset) = self.best_size
        # print("Width and hight: {}, {}".format(w, h))
        if w > 0 and h > 0:
            # self.bitmap = wx.Bitmap(self.image.Scale(w, h, self.quality))
            try:
                self.bitmap = wx.Bitmap(self.image.Scale(w, h))
            except:
                print("invalid new image size")
            # print(self.image)
            # self.Update()
            self.Refresh()

    def get_best_size(self):
        (wwidth, wheight) = self.GetSize()
        (width, height) = self.image_size

        # print("Size: {}x{}".format(width, height))
        # nwidth = float(wheight * width) / height
        # nheight = wheight
        # x_offset = (wwidth - nwidth) / 2.0
        # y_offset = 0
        # return (nwidth, nheight, x_offset, y_offset)

        if height > 0 and wheight > 0:
            if float(width) / height > float(wwidth) / wheight:
                nwidth = wwidth
                nheight = float(wwidth * height) / width
                x_offset = 0
                y_offset = (wheight - nheight) / 2.0
            else:
                nwidth = float(wheight * width) / height
                nheight = wheight
                x_offset = (wwidth - nwidth) / 2.0
                y_offset = 0
            return (nwidth, nheight, x_offset, y_offset)
        else:
            return (0.0, 0.0, 0.0, 0.0)

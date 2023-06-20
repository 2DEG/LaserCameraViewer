import wx
import time
import cv2

from events.events import PassFPS

WIDTH = 640
HEIGHT = 480
DEFAULT_BACKGROUND_COLOR = wx.BLACK


class ImageView(wx.Panel):
    """
    A panel for displaying images with additional features.
    """

    def __init__(
        self,
        parent: wx.Window,
        resize: bool = True,
        size = (-1, -1),
        black: bool = False,
        style: int = wx.NO_BORDER,
    ):
        wx.Panel.__init__(self, parent, size=(-1,-1), style=style)

        self.x_offset = 0
        self.y_offset = 0
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
            self.SetBackgroundColour(DEFAULT_BACKGROUND_COLOR)

        self.backBrush = wx.Brush(DEFAULT_BACKGROUND_COLOR, wx.SOLID)

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
        """Handles the mouse cursor entering the panel event.

        Args:
            event (wx.Event): The event instance.
        """
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
            if time.time() - self.time_start >= 1:
                self.time_start = time.time()
                wx.PostEvent(self, PassFPS(self.fps))
                self.fps = 0
            self.set_image(
                wx.ImageFromBuffer(width, height, cv2.resize(frame, (width, height)))
            )

    def refresh_bitmap(self):
        self.best_size = self.get_best_size()
        (w, h, self.x_offset, self.y_offset) = self.best_size
        if w > 0 and h > 0:
            try:
                self.bitmap = wx.Bitmap(self.image.Scale(w, h))
            except Exception as e:
                print("invalid new image size")
                print(e)
                self.bitmap = wx.Bitmap(self.default_image)
            self.Refresh()

    def get_best_size(self):
        """Calculates the best size and position for displaying the current image.

        Returns:
            tuple[float, float, float, float]: The best size and position.
        """

        (wwidth, wheight) = self.GetSize()
        (width, height) = self.image_size

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

import wx
import cv2
import os
from interface.interface import Main_Frame

from cameras.camera_av import *
import platform
from events.events import (
    EVT_MAX_FRAME_INTEN,
    EVT_PASS_FPS,
    EVT_BEAM_CENTERS,
    EVT_CAM_IMG,
    EVT_CAM_PARAM,
    EVT_CAM_INIT,
    EVT_MOUSE_XY,
)

# List all implemented camera backends
BACKENDS = ["Camera_AV", "DahuaCamera"]


# Platform check
if platform.system() == "Windows":
    from cameras.camera_dahua import *

    PLATFORM = "Windows"
elif platform.system() == "Linux":
    PLATFORM = "Linux"
    BACKENDS.pop(BACKENDS.index("DahuaCamera"))


class Frame_Handlers(Main_Frame):
    def __init__(self, *args, **kw):
        Main_Frame.__init__(self, *args, **kw)

        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Camera scan and setup
        self.camera = None
        self.backend = None
        for each in BACKENDS:
            print(each)
            camera_test = Camera_ABC(each, event_catcher=self)
            camera_cnt, camera_list = camera_test.enum_cameras()
            print("Camera cnt: ", camera_cnt, "Camera list: ", camera_list)

            if camera_cnt is None or camera_list == []:
                continue
            print("Backend", each, "is available")
            self.backend = each
            break

        if self.backend is None:
            wx.MessageBox(
                "Please connect the camera and restart the program!",
                "ERROR",
                wx.OK | wx.ICON_INFORMATION,
            )
            self.Destroy()
            wx.Exit()

        # Binds events invoked by the camera to the GUI functions
        self.Connect(-1, -1, EVT_CAM_IMG, self.panel_cam_img.player)
        self.Connect(-1, -1, EVT_CAM_PARAM, self.on_param_change)
        self.Connect(-1, -1, EVT_CAM_INIT, self.on_camera_setup_update)

        # Initialisation of recording directory
        self.rec_save_path = os.path.dirname(os.path.realpath(__file__))

        # Timers declaration
        self.rec_timer = wx.Timer(self)
        self.recording_time = int(self.video_rate.GetValue())
        self.track_timer = wx.Timer(self)
        self.tracking_time = int(self.time_bin.GetValue() * 1000)
        self.Bind(wx.EVT_TIMER, self.on_rec_timer)

        # Initial setup for exposure time and gain sliders, text boxes and status bar
        self.statusbar.SetStatusText("Cursor coord.: ({:d}, {:d})".format(0, 0), 0)
        self.statusbar.SetStatusText("Real fps: {:d}".format(0), 1)
        exp_time = 1000
        self.statusbar.SetStatusText("Real exp.: {:.2f}".format(exp_time), 2)
        self.exp_text.SetValue(str(exp_time))
        self.exp_slider.SetValue(exp_time)

        gain = 1
        self.statusbar.SetStatusText("Real gain: {:.2f}".format(gain), 3)
        self.gain_text.SetValue(str(gain))
        self.gain_slider.SetValue(gain)

        # Initial setup for the camera connection status and number of detected beams
        # in the status bar
        self.statusbar.SetStatusText("Num. of detected beams: {:d}".format(0), 4)
        self.statusbar.SetStatusText("Con. status: Connected", 5)

        # Binds events invoked video panel to status bar updates, such as
        # mouse position, fps and max intensity
        self.panel_cam_img.Connect(-1, -1, EVT_MOUSE_XY, self.on_update_mouse_xy)
        self.panel_cam_img.Connect(
            -1, -1, EVT_MAX_FRAME_INTEN, self.on_update_intensity
        )
        self.panel_cam_img.Connect(-1, -1, EVT_PASS_FPS, self.on_update_fps)

        # Binds event invoked by the detection of the beam centers
        self.panel_cam_img.Connect(-1, -1, EVT_BEAM_CENTERS, self.on_centers_update)

        # Declares intial absence of acquisition and tracking
        self.panel_cam_img.meas_on = False
        self.panel_cam_img.run_meas = False

    def on_centers_update(self, event):
        """
        Updates positions of the detected beams based on the event data.

        Args:
            event: The wxPython event containing center data.
        """
        centers = event.centers
        self.info_monitor.Clear()
        self.info_monitor.WriteText("Beams centers detected:" + "\n")
        for idx, each in enumerate(centers):
            self.info_monitor.AppendText(
                "{}. x: {}, y: {} \n".format(idx + 1, each[0], each[1])
            )

    def on_rec_start_stop(self, event):
        """
        Handles start and stop of the recording (frame sequence) based on the event data.

        Args:
            event: The wxPython event containing start/stop data.
        """
        print("Sequence Timer ID: ", self.rec_timer.Id)
        if self.t_vid.IsToggled():
            # Start recording
            self.rec_timer.Start(self.recording_time)
        else:
            self.rec_timer.Stop()

    def on_rec_timer(self, event):
        """
        Handles recording time updates based on the event data.

        Args:
            event: The wxPython event containing time update data.
        """
        if event.Id == self.rec_timer.Id:
            print("Current Event ID: ", event.Id)
            evt = wx.PyCommandEvent(
                wx.wxEVT_COMMAND_TOOL_CLICKED, self.t_scr_sht.GetId()
            )
            wx.PostEvent(self, evt)
        if event.Id == self.track_timer.Id:
            self.track_wr_point()

    def on_video_rate(self, event):
        """
        Updates the video rate based on the event data.

        Args:
            event: The wxPython event containing video rate data.
        """
        self.recording_time = int(self.video_rate.GetValue())

    def on_update_mouse_xy(self, event):
        """
        Updates mouse position is status bar based on the event data.

        Args:
            event: The wxPython event containing mouse position data.
        """

        self.statusbar.SetStatusText(
            "Cursor coord.: ({:d}, {:d})".format(event.x, event.y), 0
        )

    def on_rec_dir(self, event):
        """
        Sets the recording directory based on the event data.

        Args:
            event: The wxPython event containing directory data.
        """

        path = event.GetPath()
        if os.path.exists(path):
            self.rec_save_path = path

    def on_track_saving_dir(self, event):
        """
        Sets the directory for saving tracking data based on the event data.

        Args:
            event: The wxPython event containing directory data.
        """

        path = event.GetPath()
        if os.path.exists(path):
            self.panel_cam_img.track_path = path

    def on_screenshot(self, event):
        """
        Handles screenshot requests based on the event data.

        Args:
            event: The wxPython event containing screenshot request data.
        """

        print("Screenshot buttom pressed!")
        self.panel_cam_img.make_screenshot(self.rec_save_path)

    def on_acq_start(self, event):
        """
        Handles acquisition start requests based on the event data.

        Args:
            event: The wxPython event containing start request data.
        """

        print("Backend: ", self.backend)
        self.camera = Camera_ABC(self.backend, event_catcher=self)
        if self.camera is not None:
            self.camera.start()

    def on_acq_stop(self, event):
        """
        Handles acquisition stop requests based on the event data.

        Args:
            event: The wxPython event containing stop request data.
        """

        if self.camera is not None:
            self.camera.stop()
            self.camera = None
        self.panel_cam_img.stop()

    def on_line_len_text(self, event):
        """
        Updates cross (ellipse center marker) line length based on the event data.

        Args:
            event: The wxPython event containing line length data.
        """

        self.panel_cam_img.cross_line_len = int(event.GetValue())

    def on_tracking_appl(self, event):
        """
        Initialize laser beams tracking settings.

        Args:
            event: The wxPython event containing tracking settings data.
        """

        self.panel_cam_img.tracking_arr = []
        self.panel_cam_img.init_tracking = True

    def on_timebin_text(self, event):
        """
        Updates the time bin ([ms]) for laser beam tracking.

        Args:
            event: The wxPython event containing time bin data.
        """

        self.tracking_time = int(self.time_bin.GetValue() * 1000)

    def on_tracking_start_stop(self, event):
        """
        Handles start and stop of laser beams tracking.

        Args:
            event: The wxPython event containing start/stop data.
        """

        if self.panel_cam_img.tracking_arr == []:
            wx.MessageBox(
                "Please fix tracking start point first!",
                "INFO",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        if self.t_track.IsToggled():
            self.track_timer.Start(self.tracking_time)
        else:
            self.track_timer.Stop()

    def track_wr_point(self):
        """
        Writes the tracking point.
        """

        self.panel_cam_img.collect_centers = True

    def on_exp_enter(self, event):
        """
        Updates the camera's exposure time.

        Args:
            event: The wxPython event containing exposure time data.
        """

        new_exp_time = float(self.exp_text.GetValue())
        print("New exp_time:", new_exp_time)
        if self.camera:
            self.camera.set_exposure(new_exp_time)

    def on_gain_enter(self, event):
        """
        Updates the camera's gain.

        Args:
            event: The wxPython event containing gain data.
        """

        new_gain = float(self.gain_text.GetValue())
        print("New gain:", new_gain)
        if self.camera:
            self.camera.set_gain(new_gain)

    def on_param_change(self, event):
        """
        Handles parameter changes.

        Args:
            event: The wxPython event containing parameter change data.
        """

        param = event.param
        value = event.val
        if param == "Gain":
            self.gain_text.SetValue(str(value))
            self.gain_slider.SetValue(value)
            self.statusbar.SetStatusText("Real gain: {:.2f}".format(value), 3)
        elif param == "ExposureTime":
            self.exp_text.SetValue(str(value))
            self.exp_slider.SetValue(value)
            self.statusbar.SetStatusText("Real exp.: {:.2f}".format(value), 2)

    def on_camera_setup_update(self, event):
        """
        Updates the interface for camera specific setups.

        Args:
            event: The wxPython event containing camera setup data.
        """

        self.exp_slider.SetRange(*(map(int, event.prop["exposure_range"])))
        self.exp_slider.SetValue(int(event.prop["exposure"]))
        self.exp_text.SetRange(*(map(int, event.prop["exposure_range"])))
        self.exp_text.SetIncrement(int(event.prop["exposure_increment"]))
        self.exp_text.SetValue(int(event.prop["exposure"]))
        self.statusbar.SetStatusText(
            "Real exp.: {:.2f}".format(int(event.prop["exposure"])), 2
        )

        self.gain_slider.SetRange(*(map(int, event.prop["gain_range"])))
        self.gain_slider.SetValue(int(event.prop["gain"]))
        self.gain_text.SetRange(*(map(int, event.prop["gain_range"])))
        self.gain_text.SetIncrement(event.prop["gain_increment"])
        self.gain_text.SetValue(int(event.prop["gain"]))
        self.statusbar.SetStatusText(
            "Real gain: {:.2f}".format(int(event.prop["gain"])), 3
        )

    def on_update_fps(self, event):
        """
        Updates the frames per second in GUI.

        Args:
            event: The wxPython event containing fps data.
        """

        self.statusbar.SetStatusText("Real fps: {:d}".format(event.fps), 1)

    def on_update_intensity(self, event):
        """
        Updates the intensity in GUI.

        Args:
            event: The wxPython event containing intensity data.
        """

        self.statusbar.SetStatusText("Max. intensity: {}".format(event.intensity), 5)

    def on_close(self, event):
        """
        Handles the closing of the application based on the event data.

        Args:
            event: The wxPython event containing close request data.
        """

        if self.camera is not None:
            self.camera.stop()
        self.panel_cam_img.stop()
        cv2.destroyAllWindows()

        self.Destroy()
        wx.Exit()

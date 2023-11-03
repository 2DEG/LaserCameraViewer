import wx
import cv2
import os
from interface.interface import Main_Frame
from interface.video_view import Frame_Processor, detect_ellipses
from datetime import datetime
import threading
import itertools
import csv

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
BACKENDS = ["Camera_AV", "DahuaCamera", "Camera_ADF"]


# Platform check
if platform.system() == "Windows":
    try:
        from cameras.camera_dahua import *
    except:
        BACKENDS.pop(BACKENDS.index("DahuaCamera"))
    PLATFORM = "Windows"
elif platform.system() == "Linux":
    PLATFORM = "Linux"
    BACKENDS.pop(BACKENDS.index("DahuaCamera"))

try:
    from cameras.camera_av import *
except:
    BACKENDS.pop(BACKENDS.index("Camera_AV"))

try:
    from cameras.camera_adf import *
except:
    BACKENDS.pop(BACKENDS.index("Camera_ADF"))

def find_closest_centers(reference = [], array = []):
    """
    For each circle center in array1, find the closest circle center in array2.
    Stores the result in the result_container at the given index.
    :param array1: List of tuples representing the circle centers (x, y) in the first array
    :param array2: List of tuples representing the circle centers (x, y) in the second array
    :param result_container: List to store the result
    :param index: Index in the result container where the result will be stored
    """
    closest_centers = []
    indexes = ()

    if len(array) == 0:
        if len(reference) != 0:
            return [(idx, None) for idx in range(len(reference))]

    if len(reference) <= len(array):
        for idx, center1 in enumerate(reference):
            # Calculate distances from the current center to all centers in the second array
            distances = [np.linalg.norm(np.array(center1) - np.array(center2)) for center2 in array]
            # Find the index of the closest center in array2
            closest_index = np.argmin(distances)
            closest_centers.append((idx, closest_index))
    else:
         for idx, center1 in enumerate(array):
            # Calculate distances from the current center to all centers in the second array
            distances = [np.linalg.norm(np.array(center1) - np.array(center2)) for center2 in reference]
            # Find the index of the closest center in array2
            closest_index = np.argmin(distances)
            closest_centers.append((closest_index, idx)) 

    if len(closest_centers) < len(reference):
        a = []
        for each in closest_centers:
            a.append(each[0])
        for idx, _ in enumerate(reference):
            if idx not in a:
                closest_centers.append((idx, None))
    
    return closest_centers

def write_tracking_data(time, tracking_file, tracking_arr, fixed_arr):
    closest_centers = find_closest_centers(fixed_arr, tracking_arr)
    wrt_arr = [time]

    for each in closest_centers:
        if each[1] is None:
            wrt_arr.append(None)
            wrt_arr.append(None)
        else:
            fixed_arr[each[0]] = tracking_arr[each[1]]
            wrt_arr.append(tracking_arr[each[1]][0])
            wrt_arr.append(tracking_arr[each[1]][1])

    print("Write array: ", wrt_arr)

    with open(tracking_file, "a") as my_csv:
            csvWriter = csv.writer(my_csv, delimiter=",")
            csvWriter.writerow(wrt_arr)
            print("Point ", wrt_arr, "saved!")


class Frame_Handlers(Main_Frame):
    def __init__(self, *args, **kw):
        Main_Frame.__init__(self, *args, **kw)

        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Camera scan and setup
        self.camera = None
        self.backend = None

        if BACKENDS == []:
            wx.MessageBox(
                "Can not find cameras drivers. Please install drivers and restart the program.",
                "ERROR",
                wx.OK | wx.ICON_ERROR,
            )
            self.Destroy()
            wx.Exit()

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
                "Can not find any camera. Please check the connection and restart the program.",
                "ERROR",
                wx.OK | wx.ICON_ERROR,
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
        # self.statusbar.SetStatusText("Con. status: Connected", 5)

        # Binds events invoked video panel to status bar updates, such as
        # mouse position, fps and max intensity
        self.panel_cam_img.Connect(-1, -1, EVT_MOUSE_XY, self.on_update_mouse_xy)
        self.Connect(
            -1, -1, EVT_MAX_FRAME_INTEN, self.on_update_intensity
        )
        self.panel_cam_img.Connect(-1, -1, EVT_PASS_FPS, self.on_update_fps)

        # Binds event invoked by the detection of the beam centers
        self.Connect(-1, -1, EVT_BEAM_CENTERS, self.on_centers_update)

        # Declares intial absence of acquisition and tracking
        self.panel_cam_img.meas_on = False
        self.panel_cam_img.run_meas = False
        self.track_path = os.path.dirname(os.path.realpath(__file__))

    def on_centers_update(self, event):
        """
        Updates positions of the detected beams.

        Args:
            event: The wxPython event containing center data.
        """
        centers = event.centers
        # print("Centers: ", centers)
        self.info_monitor.Clear()
        self.info_monitor.WriteText("Beams centers detected:" + "\n")
        for idx, each in enumerate(centers):
            self.info_monitor.AppendText(
                "{}. x: {}, y: {} \n".format(idx + 1, each[0], each[1])
            )
        self.statusbar.SetStatusText("Num. of detected beams: {:d}".format(len(centers)), 4)

    def on_rec_start_stop(self, event):
        """
        Handles start and stop of the recording (frame sequence).

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
        Handles recording time updates.

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
            self.dt += self.tracking_time/1000
            self.update_tracking_data(time = self.dt)

    def on_video_rate(self, event):
        """
        Updates the video rate.

        Args:
            event: The wxPython event containing video rate data.
        """
        self.recording_time = int(self.video_rate.GetValue())

    def on_update_mouse_xy(self, event):
        """
        Updates mouse position at the status bar.

        Args:
            event: The wxPython event containing mouse position data.
        """

        self.statusbar.SetStatusText(
            "Cursor coord.: ({:d}, {:d})".format(event.x, event.y), 0
        )

    def on_rec_dir(self, event):
        """
        Sets the recording directory.

        Args:
            event: The wxPython event containing directory data.
        """

        path = event.GetPath()
        if os.path.exists(path):
            self.rec_save_path = path

    def on_track_saving_dir(self, event):
        """
        Sets the directory for saving tracking data.

        Args:
            event: The wxPython event containing directory data.
        """

        path = event.GetPath()
        if os.path.exists(path):
            self.track_path = path

    def on_screenshot(self, event):
        """
        Handles screenshot requests.

        Args:
            event: The wxPython event containing screenshot request data.
        """

        print("Screenshot buttom pressed!")
        self.panel_cam_img.make_screenshot(self.rec_save_path)

    def on_acq_start(self, event):
        """
        Handles acquisition start requests.

        Args:
            event: The wxPython event containing start request data.
        """

        print("Backend: ", self.backend)
        self.frame_queue = queue.Queue()
        self.camera = Camera_ABC(self.backend, event_catcher=self, frame_queue=self.frame_queue)
        self.processor = Frame_Processor(frame_queue=self.frame_queue, event_catcher=self)
        if self.camera is not None:
            self.camera.start()
            self.processor.start()

    def on_acq_stop(self, event):
        """
        Handles acquisition stop requests.

        Args:
            event: The wxPython event containing stop request data.
        """

        if self.camera is not None:
            self.camera.stop()
            self.processor.stop()
            self.camera = None
        self.panel_cam_img.stop()

    def on_line_len_text(self, event):
        """
        Updates cross (ellipse center marker) line length.

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

        self.tracking_arr = []
        self.tracking_fixed_arr = []
        self.dt = self.tracking_time/1000
        if os.path.exists(self.track_path):
            print("Tracking path is valid!")
            dt = datetime.now().strftime("Track_%d%m%Y_%Hh%Mm%Ss")
            self.tracking_file = os.path.join(self.track_path, "{}.csv".format(dt))
            self.tracking_fixed_arr = self.panel_cam_img.ellipses_centers

            with open(self.tracking_file, "a") as my_csv:
                csvWriter = csv.writer(my_csv, delimiter=",")
                header = ['Time [s]']
                for idx, each in enumerate(self.panel_cam_img.ellipses_centers):
                    header.append('x{}'.format(idx))
                    header.append('y{}'.format(idx)) 
                    #
                print("Header: ", header)
                csvWriter.writerow(header)
            
            self.update_tracking_data()

    def update_tracking_data(self, time = 0.0):
        """
        Updates tracking data and write to a csv file.

        Args:
            data: New tracking data to be appended.
        """

        self.tracking_arr = self.panel_cam_img.ellipses_centers
        thread = threading.Thread(target=write_tracking_data, args=(time, self.tracking_file, self.tracking_arr, self.tracking_fixed_arr))
        thread.start()

        # with open(self.tracking_file, "a") as my_csv:
        #     csvWriter = csv.writer(my_csv, delimiter=",")
        #     csvWriter.writerows(self.panel_cam_img.ellipses_centers)
        #     print("Point ", self.panel_cam_img.ellipses_centers, "saved!")

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

        if self.tracking_arr == []:
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

    def on_exp_enter(self, event):
        """
        Updates the camera's exposure time.

        Args:
            event: The wxPython event containing exposure time data.
        """

        new_exp_time = float(self.exp_text.GetValue())
        print("New exp_time:", new_exp_time)
        if self.camera:
            if self.backend == "Camera_ADF":
                self.camera.set_exposure(int(new_exp_time))
            else:
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
        # print("Intensity: ", event.intensity)
        self.statusbar.SetStatusText("Max. intensity: {}".format(event.intensity), 5)

    def on_close(self, event):
        """
        Handles the closing of the application.

        Args:
            event: The wxPython event containing close request data.
        """

        if self.camera is not None:
            self.camera.stop()
        self.panel_cam_img.stop()
        cv2.destroyAllWindows()

        self.Destroy()
        wx.Exit()

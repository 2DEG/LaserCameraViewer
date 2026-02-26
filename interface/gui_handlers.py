import wx
import cv2
import os
import math
import queue
import logging
import numpy as np
from interface.interface import Main_Frame
from interface.video_view import Frame_Processor
from datetime import datetime
import threading
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
    except Exception:
        BACKENDS.pop(BACKENDS.index("DahuaCamera"))
elif platform.system() == "Linux":
    BACKENDS.pop(BACKENDS.index("DahuaCamera"))

try:
    from cameras.camera_av import *
except Exception:
    BACKENDS.pop(BACKENDS.index("Camera_AV"))

try:
    from cameras.camera_adf import *
except Exception:
    BACKENDS.pop(BACKENDS.index("Camera_ADF"))

# Define logger AFTER wildcard imports so it doesn't get overwritten
logger = logging.getLogger(__name__)

def find_closest_centers(reference=None, array=None):
    """
    For each circle center in reference, find the closest circle center in array.
    :param reference: List of tuples representing the reference circle centers (x, y)
    :param array: List of tuples representing the detected circle centers (x, y)
    """
    if reference is None:
        reference = []
    if array is None:
        array = []
    closest_centers = []

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

def _write_csv_row(tracking_file, row):
    """Write a single row to the tracking CSV file (runs in background thread)."""
    with open(tracking_file, "a") as my_csv:
        csvWriter = csv.writer(my_csv, delimiter=",")
        csvWriter.writerow(row)
    logger.debug("Tracking point saved: %s", row)


class Frame_Handlers(Main_Frame):
    def __init__(self, *args, **kw):
        Main_Frame.__init__(self, *args, **kw)

        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Camera scan and setup
        self.camera = None
        self.backend = None
        self.processor = None

        if BACKENDS == []:
            wx.MessageBox(
                "Can not find cameras drivers. Please install drivers and restart the program.",
                "ERROR",
                wx.OK | wx.ICON_ERROR,
            )
            self.Destroy()
            wx.Exit()

        for each in BACKENDS:
            logger.info("Probing backend: %s", each)
            try:
                camera_test = Camera_ABC(each, event_catcher=self)
                camera_cnt, camera_list = camera_test.enum_cameras()
            except Exception as e:
                logger.warning("Backend %s failed: %s", each, e)
                continue
            logger.info("Backend %s: found %s camera(s): %s", each, camera_cnt, camera_list)

            if camera_cnt is None or camera_list == []:
                continue
            logger.info("Using backend: %s", each)
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
        self.Connect(-1, -1, EVT_CAM_IMG, self._on_cam_image)
        self.Connect(-1, -1, EVT_CAM_PARAM, self.on_param_change)
        self.Connect(-1, -1, EVT_CAM_INIT, self.on_camera_setup_update)
        self._waiting_for_frame = False

        # Initialisation of recording directory
        self.rec_save_path = os.path.dirname(os.path.realpath(__file__))

        # Timers declaration
        self.rec_timer = wx.Timer(self)
        self.recording_time = int(self.video_rate.GetValue())
        self.track_timer = wx.Timer(self)
        self.tracking_time = int(self.time_bin.GetValue() * 1000)
        self.Bind(wx.EVT_TIMER, self.on_rec_timer)

        # Log-scale exposure slider parameters (will be updated by on_camera_setup_update)
        self._exp_min = 1.0
        self._exp_max = 1e6
        self._exp_slider_steps = 1000  # internal slider range 0..1000

        # Initial setup for exposure time and gain sliders, text boxes and status bar
        self.statusbar.SetStatusText("Cursor coord.: ({:d}, {:d})".format(0, 0), 0)
        self.statusbar.SetStatusText("Real fps: {:d}".format(0), 1)
        exp_time = 1000
        self.statusbar.SetStatusText("Real exp.: {:.2f}".format(exp_time), 2)
        self.exp_text.SetValue(str(exp_time))
        self.exp_slider.SetValue(self._exp_to_slider(exp_time))

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
        self.panel_cam_img.Connect(
            -1, -1, EVT_MAX_FRAME_INTEN, self.on_update_intensity
        )
        self.panel_cam_img.Connect(-1, -1, EVT_PASS_FPS, self.on_update_fps)

        # Binds event invoked by the detection of the beam centers
        self.Connect(-1, -1, EVT_BEAM_CENTERS, self.on_centers_update)

        # Declares initial absence of acquisition and tracking
        self.panel_cam_img.meas_on = False
        self.panel_cam_img.run_meas = False
        self.track_path = os.path.dirname(os.path.realpath(__file__))
        self.tracking_arr = []
        self.tracking_fixed_arr = []
        self.tracking_file = None

        # Track overlay state
        self.show_tracks = False
        self.track_overlay_data = None

    def on_help_tracking(self, event):
        """Shows step-by-step instructions for using the tracking tool."""
        msg = (
            "How to use the Beam Tracking tool:\n"
            "\n"
            "1. Start acquisition by pressing the Play button.\n"
            "2. Go to the 'Stability Tracking' tab.\n"
            "3. Adjust detection parameters (Max spots, Min area, Threshold)\n"
            "   until the beams you want to track are detected.\n"
            "4. Check 'Show/Hide Ellipses' to see the detected spots.\n"
            "5. Set the time period (bin size) for how often positions\n"
            "   are recorded.\n"
            "6. Choose a directory in 'Save TRACK to'.\n"
            "7. Click 'Apply' to fix the current beam positions as\n"
            "   the reference. A CSV file will be created.\n"
            "8. Press the Track button in the toolbar to start/stop\n"
            "   recording beam positions over time.\n"
            "\n"
            "The CSV file will contain timestamps and (x, y) coordinates\n"
            "for each tracked beam."
        )
        wx.MessageBox(msg, "Tracking Guide", wx.OK | wx.ICON_INFORMATION)

    def _on_cam_image(self, event):
        """Wrapper for camera image events. Dismisses the start-up progress
        dialog when the first frame arrives, then forwards to the player."""
        if self._waiting_for_frame:
            self._dismiss_busy_dialog()
        self.panel_cam_img.player(event)

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
        logger.debug("Sequence Timer ID: %s", self.rec_timer.Id)
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
            logger.debug("Recording timer tick (ID: %s)", event.Id)
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

    def on_show_tracks_chk(self, event):
        """
        Toggles the track overlay display and enables/disables the track file picker.

        Args:
            event: The wxPython checkbox event.
        """
        self.show_tracks = self.show_tracks_chk.GetValue()
        self.m_staticText_open_track.Enable(self.show_tracks)
        self.m_filePicker_track.Enable(self.show_tracks)
        if not self.show_tracks:
            self.track_overlay_data = None
            self.panel_cam_img.track_overlay = None

    def on_track_file_picked(self, event):
        """
        Loads a track CSV file and sets the overlay data for drawing on the
        camera view.

        Args:
            event: The wxPython file picker event.
        """
        path = event.GetPath()
        if not os.path.isfile(path):
            return
        try:
            with open(path, "r") as f:
                reader = csv.reader(f)
                header = next(reader)
                # Number of beams = (columns - 1) / 2  (Time, x0, y0, x1, y1, ...)
                num_beams = (len(header) - 1) // 2
                if num_beams <= 0:
                    return

                tracks = [[] for _ in range(num_beams)]
                initial = None

                for row in reader:
                    if len(row) < 1 + num_beams * 2:
                        continue
                    points = []
                    skip_row = False
                    for i in range(num_beams):
                        x_str = row[1 + i * 2].strip()
                        y_str = row[2 + i * 2].strip()
                        if x_str == "" or y_str == "":
                            skip_row = True
                            break
                        try:
                            points.append((int(float(x_str)), int(float(y_str))))
                        except ValueError:
                            skip_row = True
                            break
                    if skip_row:
                        continue
                    if initial is None:
                        initial = list(points)
                    for idx, pt in enumerate(points):
                        tracks[idx].append(pt)

                if initial is not None:
                    self.track_overlay_data = {
                        "initial": initial,
                        "tracks": tracks,
                    }
                    self.panel_cam_img.track_overlay = self.track_overlay_data
                    logger.info("Loaded track overlay: %d beams, %d points",
                                num_beams, len(tracks[0]) if tracks else 0)
        except Exception as e:
            logger.error("Failed to load track file %s: %s", path, e)
            wx.MessageBox(
                f"Failed to load track file:\n{e}",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

    def on_screenshot(self, event):
        """
        Handles screenshot requests.

        Args:
            event: The wxPython event containing screenshot request data.
        """

        logger.info("Screenshot requested")
        self.panel_cam_img.make_screenshot(self.rec_save_path)

    def on_acq_start(self, event):
        """
        Handles acquisition start requests. Shows a progress dialog until
        the first frame arrives from the camera.

        Args:
            event: The wxPython event containing start request data.
        """

        if self.camera is not None:
            logger.warning("Acquisition already running, ignoring start request")
            return

        logger.info("Starting acquisition with backend: %s", self.backend)
        self.frame_queue = queue.Queue(maxsize=2)
        self.command_queue = queue.Queue()
        self.camera = Camera_ABC(self.backend, event_catcher=self, frame_queue=self.frame_queue)
        self.processor = Frame_Processor(
            frame_queue=self.frame_queue,
            command_queue=self.command_queue,
            event_catcher=self,
            cross_line_len=int(self.line_len.GetValue()),
            detect_ellipses=self.show_ellps_chk.GetValue(),
            max_spots=self.max_spots.GetValue(),
            min_area=self.min_area.GetValue(),
            threshold=self.det_threshold.GetValue(),
        )
        if self.camera is not None:
            # Show progress dialog while waiting for the camera to start
            self._busy_dlg = wx.ProgressDialog(
                "Starting Camera",
                "Connecting to camera and starting stream...",
                maximum=100,
                parent=self,
                style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT,
            )
            self._busy_timer = wx.Timer(self)
            self._busy_timeout = 0
            self.Bind(wx.EVT_TIMER, self._on_busy_pulse, self._busy_timer)
            self._busy_timer.Start(100)
            self._waiting_for_frame = True

            self.camera.start()
            self.processor.start()

    def _on_busy_pulse(self, event):
        """Pulses the progress dialog and checks for first frame or timeout."""
        if event.GetTimer().GetId() != self._busy_timer.GetId():
            # Pass through to other timer handlers (rec_timer, track_timer)
            self.on_rec_timer(event)
            return
        self._busy_timeout += 100
        if not self._waiting_for_frame or self._busy_timeout > 15000:
            # First frame arrived or 15s timeout
            self._dismiss_busy_dialog()
            return
        keep_going, _ = self._busy_dlg.Pulse()
        if not keep_going:
            # User pressed Cancel
            self._dismiss_busy_dialog()
            self.on_acq_stop(None)

    def _dismiss_busy_dialog(self):
        """Stops the busy timer and closes the progress dialog."""
        if hasattr(self, '_busy_timer') and self._busy_timer.IsRunning():
            self._busy_timer.Stop()
        if hasattr(self, '_busy_dlg') and self._busy_dlg:
            self._busy_dlg.Destroy()
            self._busy_dlg = None
        self._waiting_for_frame = False

    def on_acq_stop(self, event):
        """
        Handles acquisition stop requests. Shows a progress dialog while
        the camera threads are shutting down.

        Args:
            event: The wxPython event containing stop request data.
        """

        if self.camera is not None:
            dlg = wx.ProgressDialog(
                "Stopping Camera",
                "Stopping camera stream...",
                maximum=100,
                parent=self,
                style=wx.PD_APP_MODAL,
            )
            dlg.Pulse()

            def _stop_worker():
                self.camera.stop()
                self.processor.stop()
                wx.CallAfter(_stop_done)

            def _stop_done():
                self.camera = None
                self.processor = None
                self.panel_cam_img.stop()
                dlg.Destroy()

            threading.Thread(target=_stop_worker, daemon=True).start()
        else:
            self.panel_cam_img.stop()

    def on_show_ellps_chk(self, event):
        if self.processor:
            self.command_queue.put({"detect_ellipses": self.show_ellps_chk.GetValue()})

    def on_line_len_text(self, event):
        """
        Updates cross (ellipse center marker) line length.

        Args:
            event: The wxPython event containing line length data.
        """

        cross_line_len = int(self.line_len.GetValue())
        if self.processor:
            self.command_queue.put({"cross_line_len": cross_line_len})

    def on_detection_params(self, event):
        """
        Updates spot detection parameters (max spots, min area, threshold).

        Args:
            event: The wxPython event from any of the detection SpinCtrl widgets.
        """

        if self.processor:
            self.command_queue.put({"max_spots": self.max_spots.GetValue()})
            self.command_queue.put({"min_area": self.min_area.GetValue()})
            self.command_queue.put({"threshold": self.det_threshold.GetValue()})

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
            logger.info("Tracking path valid: %s", self.track_path)
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
                logger.debug("Tracking header: %s", header)
                csvWriter.writerow(header)
            
            self.update_tracking_data()

    def update_tracking_data(self, time=0.0):
        """
        Updates tracking data and writes to a csv file.

        Args:
            time: Timestamp for the tracking data point.
        """

        self.tracking_arr = self.panel_cam_img.ellipses_centers
        # Compute matching on the main thread (fast, avoids race condition)
        closest_centers = find_closest_centers(self.tracking_fixed_arr, self.tracking_arr)
        row = [time]
        for each in closest_centers:
            if each[1] is None:
                row.append(None)
                row.append(None)
            else:
                self.tracking_fixed_arr[each[0]] = self.tracking_arr[each[1]]
                row.append(self.tracking_arr[each[1]][0])
                row.append(self.tracking_arr[each[1]][1])

        logger.debug("Write array: %s", row)
        # Offload only the file I/O to a background thread
        threading.Thread(
            target=_write_csv_row,
            args=(self.tracking_file, row),
            daemon=True,
        ).start()

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

    def _exp_to_slider(self, exposure):
        """Convert an exposure value to a log-scale slider position (0..N)."""
        if exposure <= self._exp_min:
            return 0
        if exposure >= self._exp_max:
            return self._exp_slider_steps
        return int(self._exp_slider_steps
                   * math.log(exposure / self._exp_min)
                   / math.log(self._exp_max / self._exp_min))

    def _slider_to_exp(self, pos):
        """Convert a log-scale slider position (0..N) to an exposure value."""
        return self._exp_min * (self._exp_max / self._exp_min) ** (pos / self._exp_slider_steps)

    def on_exp_slider(self, event):
        """
        Updates the camera's exposure time from the slider (log scale).

        Args:
            event: The wxPython slider event.
        """

        new_exp_time = self._slider_to_exp(self.exp_slider.GetValue())
        self.exp_text.SetValue(float(new_exp_time))
        if self.camera:
            if self.backend == "Camera_ADF":
                self.camera.set_exposure(int(new_exp_time))
            else:
                self.camera.set_exposure(float(new_exp_time))

    def on_exp_enter(self, event):
        """
        Updates the camera's exposure time from the text input.

        Args:
            event: The wxPython event containing exposure time data.
        """

        # Defer reading the value so the control commits the typed text first
        wx.CallAfter(self._apply_exposure)

    def _apply_exposure(self):
        new_exp_time = float(self.exp_text.GetValue())
        self.exp_slider.SetValue(self._exp_to_slider(new_exp_time))
        if self.camera:
            if self.backend == "Camera_ADF":
                self.camera.set_exposure(int(new_exp_time))
            else:
                self.camera.set_exposure(new_exp_time)

    def on_gain_slider(self, event):
        """
        Updates the camera's gain from the slider.

        Args:
            event: The wxPython slider event.
        """

        new_gain = self.gain_slider.GetValue()
        self.gain_text.SetValue(float(new_gain))
        if self.camera:
            self.camera.set_gain(float(new_gain))

    def on_gain_enter(self, event):
        """
        Updates the camera's gain from the text input.

        Args:
            event: The wxPython event containing gain data.
        """

        # Defer reading the value so the control commits the typed text first
        wx.CallAfter(self._apply_gain)

    def _apply_gain(self):
        new_gain = float(self.gain_text.GetValue())
        self.gain_slider.SetValue(int(new_gain))
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
            self.gain_text.SetValue(float(value))
            self.gain_slider.SetValue(int(value))
            self.statusbar.SetStatusText("Real gain: {:.2f}".format(value), 3)
        elif param == "ExposureTime":
            self.exp_text.SetValue(float(value))
            self.exp_slider.SetValue(self._exp_to_slider(value))
            self.statusbar.SetStatusText("Real exp.: {:.2f}".format(value), 2)

    def on_camera_setup_update(self, event):
        """
        Updates the interface for camera specific setups.

        Args:
            event: The wxPython event containing camera setup data.
        """

        self._exp_min = max(1.0, float(event.prop["exposure_range"][0]))
        self._exp_max = float(event.prop["exposure_range"][1])
        self.exp_slider.SetRange(0, self._exp_slider_steps)
        self.exp_slider.SetValue(self._exp_to_slider(event.prop["exposure"]))
        self.exp_text.SetRange(*(map(int, event.prop["exposure_range"])))
        self.exp_text.SetIncrement(float(event.prop["exposure_increment"]))
        self.exp_text.SetValue(float(event.prop["exposure"]))
        self.statusbar.SetStatusText(
            "Real exp.: {:.2f}".format(event.prop["exposure"]), 2
        )

        self.gain_slider.SetRange(*(map(int, event.prop["gain_range"])))
        self.gain_slider.SetValue(int(event.prop["gain"]))
        self.gain_text.SetRange(*(map(int, event.prop["gain_range"])))
        self.gain_text.SetIncrement(float(event.prop["gain_increment"]))
        self.gain_text.SetValue(float(event.prop["gain"]))
        self.statusbar.SetStatusText(
            "Real gain: {:.2f}".format(event.prop["gain"]), 3
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
        Handles the closing of the application.

        Args:
            event: The wxPython event containing close request data.
        """

        if self.camera is not None:
            self.camera.stop()
        if self.processor is not None:
            self.processor.stop()
        self.panel_cam_img.stop()
        cv2.destroyAllWindows()

        self.Destroy()
        wx.Exit()

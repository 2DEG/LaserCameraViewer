import wx
import cv2
import os
from interface.interface import Main_Frame, Camera_Options_Frame

from cameras.camera_av import *
import platform
from events.events import (
    EVT_ON_CROP,
    EVT_ENOUGH_POINTS,
    EVT_NOT_ENOUGH_POINTS,
    EVT_UPDT_CAM,
    EVT_CALIBRATION,
    EVT_LENS_CALIBRATION,
    EVT_MAX_FRAME_INTEN,
    EVT_PASS_FPS,
    EVT_BEAM_CENTERS,
    OnLensCalibrationStop,
    UpdateCamera,
    OnCalibration,
    OnLensCalibrationInit,
    EVT_CAM_IMG,
    EVT_CAM_PARAM,
    EVT_CAM_INIT,
)

BACKENDS = ["Camera_AV", "DahuaCamera"]

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

        self.camera = None
        for each in BACKENDS:
            print(each)
            camera_test = Camera_ABC(each)
            camera_cnt, camera_list = camera_test.enum_cameras()
            print('Camera cnt: ', camera_cnt, 'Camera list: ', camera_list)

            if camera_cnt is None or camera_list == []:
                continue
            print("Backend", each, "is available")
            self.backend = each
            break


        self.Connect(-1, -1, EVT_CAM_IMG, self.panel_cam_img.player)
        self.Connect(-1, -1, EVT_CAM_PARAM, self.on_param_change)
        self.Connect(-1, -1, EVT_CAM_INIT, self.on_camera_setup_update)

        # self.camera = None ## TODO Check if the camera is set, when starting the acquis.
        # self.backend = None
        self.stream_source = None
        self.rec_save_path = os.path.dirname(os.path.realpath(__file__))

        # Timers declaration
        self.rec_timer = wx.Timer(self)
        self.recording_time = int(self.video_rate.GetValue())
        # self.video_timer = wx.Timer(self)
        self.track_timer = wx.Timer(self)
        self.tracking_time = int(self.time_bin.GetValue() * 1000)
        self.Bind(wx.EVT_TIMER, self.on_rec_timer)
        # self.timer.Start(1000./fps)
        # self.Bind(wx.EVT_TIMER, self.on_timer)

        # self.camera = Camera(0)

        # self.camera.set_resolution(2592, 2048)

        # self.t_stop.Enable(False)

        self.statusbar.SetStatusText("Cursor coord.: ({:d}, {:d})".format(0, 0), 0)
        self.statusbar.SetStatusText("Real fps: {:d}".format(0), 1)
        # exp_time = getExposureTime(self.camera)
        exp_time = 1000
        self.statusbar.SetStatusText("Real exp.: {:.2f}".format(exp_time), 2)
        self.exp_text.SetValue(str(exp_time))
        self.exp_slider.SetValue(exp_time)

        # gain = getGain(self.camera)
        gain = 1
        self.statusbar.SetStatusText("Real gain: {:.2f}".format(gain), 3)
        self.gain_text.SetValue(str(gain))
        self.gain_slider.SetValue(gain)

        self.statusbar.SetStatusText("Num. of detected beams: {:d}".format(0), 4)
        self.statusbar.SetStatusText("Con. status: Connected", 5)

        # self.panel_cam_img.Connect(-1, -1, EVT_ON_CROP, self.on_crop)t
        self.panel_cam_img.Connect(
            -1, -1, EVT_MAX_FRAME_INTEN, self.on_update_intensity
        )
        self.panel_cam_img.Connect(-1, -1, EVT_PASS_FPS, self.on_update_fps)
        self.panel_cam_img.Connect(-1, -1, EVT_BEAM_CENTERS, self.on_centers_update)
        # self.Connect(-1, -1, EVT_UPDT_CAM, self.on_camera_setup_update)

        # self.panel_cam_img.callback = self.capture
        # self.panel_cam_img.callback = lambda : get_frame(self.stream_source)
        self.panel_cam_img.meas_on = False
        self.panel_cam_img.run_meas = False
        print("Pre Start")
        # self.panel_cam_img.start()

    def on_centers_update(self, event):
        # print(event.centers)
        centers = event.centers
        # message = ''
        self.info_monitor.Clear()
        self.info_monitor.WriteText("Beams centers detected:" + "\n")
        for idx, each in enumerate(centers):
            self.info_monitor.AppendText(
                "{}. x: {}, y: {} \n".format(idx + 1, each[0], each[1])
            )

        # self.info_monitor.SetValue(message)

    def on_rec_start_stop(self, event):
        print("Sequence Timer ID: ", self.rec_timer.Id)
        if self.t_vid.IsToggled():
            # Start recording
            self.rec_timer.Start(self.recording_time)
        else:
            self.rec_timer.Stop()
            # Stop recording
        # print("Is toggled? ", self.t_vid.IsToggled())

    def on_rec_timer(self, event):
        if event.Id == self.rec_timer.Id:
            print("Current Event ID: ", event.Id)
            evt = wx.PyCommandEvent(
                wx.wxEVT_COMMAND_TOOL_CLICKED, self.t_scr_sht.GetId()
            )
            wx.PostEvent(self, evt)
        if event.Id == self.track_timer.Id:
            self.track_wr_point()
        # .GetEventHandler().ProcessEvent()

    def on_video_rate(self, event):
        # print(event.GetPosition())
        self.recording_time = int(self.video_rate.GetValue())
        # self.tracking_time = int(event.GetPosition())
        # return

    def on_rec_dir(self, event):
        path = event.GetPath()
        if os.path.exists(path):
            self.rec_save_path = path

    def on_track_saving_dir(self, event):
        path = event.GetPath()
        if os.path.exists(path):
            self.panel_cam_img.track_path = path

    def on_screenshot(self, event):
        print("Screenshot buttom pressed!")
        self.panel_cam_img.make_screenshot(self.rec_save_path)

    def on_acq_start(self, event):
        print("Backend: ", self.backend)
        self.camera = Camera_ABC(self.backend, event_catcher=self)
        # self.camera.event_catcher = self
        if self.camera is not None:
            self.camera.start()

    def on_acq_stop(self, event):
        if self.camera is not None:
            self.camera.stop()
            self.camera = None
        self.panel_cam_img.stop()

    def on_line_len_text(self, event):
        self.panel_cam_img.cross_line_len = int(event.GetValue())

    def on_tracking_appl(self, event):
        self.panel_cam_img.tracking_arr = []
        self.panel_cam_img.init_tracking = True

    def on_timebin_text(self, event):
        self.tracking_time = int(self.time_bin.GetValue() * 1000)

    def on_tracking_start_stop(self, event):
        if self.panel_cam_img.tracking_arr == []:
            wx.MessageBox(
                "Please fix tracking start point first!",
                "INFO",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        if self.t_track.IsToggled():
            # Start recording
            self.track_timer.Start(self.tracking_time)
            # self.panel_cam_img.collect_centers = True
        else:
            self.track_timer.Stop()
            # self.panel_cam_img.collect_centers = False
            # print('Track: ', self.panel_cam_img.tracking_arr)
        # return super().on_tracking_start_stop(event)

    def track_wr_point(self):
        self.panel_cam_img.collect_centers = True

    def on_exp_enter(self, event):
        new_exp_time = float(self.exp_text.GetValue())
        print("New exp_time:", new_exp_time)
        if self.camera:
            self.camera.set_exposure(new_exp_time)
        # self.statusbar.SetStatusText("Real exp.: {:.2f}".format(exp_time), 2)
        # self.exp_slider.SetValue(exp_time)

    def on_gain_enter(self, event):
        new_gain = float(self.gain_text.GetValue())
        print("New gain:", new_gain)
        if self.camera:
            self.camera.set_gain(new_gain)
        # print(type(gain))
        # self.statusbar.SetStatusText("Real gain: {:.2f}".format(gain), 3)
        # self.gain_slider.SetValue(gain)

    def on_param_change(self, event):
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
        self.statusbar.SetStatusText("Real fps: {:d}".format(event.fps), 1)

    def on_update_intensity(self, event):
        self.statusbar.SetStatusText("Max. intensity: {}".format(event.intensity), 5)

    def on_close(self, event):
        if self.camera is not None:
            self.camera.stop()
        self.panel_cam_img.stop()
        cv2.destroyAllWindows()

        self.Destroy()
        wx.Exit()

    def opt_cam_start(self, event):
        options = Camera_Options_Handler(parent=self)
        options.Show()
        print("Non blocking")


class Camera_Options_Handler(Camera_Options_Frame):
    def __init__(self, *args, parent=None, **kw):
        Camera_Options_Frame.__init__(self, *args, parent=None, **kw)
        self.parent = parent
        # self.devices = FilterGraph().get_input_devices()
        # self.cameras_list.Set(self.devices)
        # self.cameras_list.SetSelection(0)
        # print(self.devices)

    def on_apply(self, event):
        # camera_id = self.cameras_list.GetString(self.cameras_list.GetSelection())
        backend = self.backends_list.GetString(self.backends_list.GetSelection())
        self.camera = Camera("Camera_AV")  # Setup camera object
        self.parent.gain_slider.SetRange(*self.camera.param_list["gain_range"])
        self.parent.gain_text.SetIncrement(self.camera.param_list["gain_increment"])
        self.parent.exp_slider.SetRange(*self.camera.param_list["exposure_range"])
        self.parent.exp_text.SetIncrement(self.camera.param_list["exposure_increment"])

    def on_close(self, event):
        self.Destroy()

    def on_cancel(self, event):
        self.Destroy()

    def __del__(self):
        pass

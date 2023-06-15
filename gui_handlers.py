import wx
import cv2
import os
import csv
from interface import Main_Frame, Camera_Options_Frame

# from pygrabber.dshow_graph import FilterGraph
# from camera import Camera
# from camera_hard_core import *
from camera_primitive import *
from events import (
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
	EVT_CAM_PARAM
)
import numpy as np

# import wx.grid as grd

# from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas  # type: ignore
# from matplotlib.figure import Figure
# import matplotlib.pyplot as plt


class Frame_Handlers(Main_Frame):
	def __init__(self, *args, **kw):
		Main_Frame.__init__(self, *args, **kw)

		self.Bind(wx.EVT_CLOSE, self.on_close)


		self.camera = None
		self.backend = "Camera_AV"
		self.Connect(-1, -1, EVT_CAM_IMG, self.panel_cam_img.player)
		self.Connect(-1, -1, EVT_CAM_PARAM, self.on_param_change)

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
		self.camera = Camera(self.backend)
		self.camera.event_catcher = self
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

	# def __del__( self ):
	# 	if self.stream_source is not None:
	# 		self.panel_cam_img.stop()
	# 		# self.camera.disconnect()
	# 		stop_grabbing(self.stream_source)
	# 		close_stream_source(self.stream_source, self.camera)
	# 	cv2.destroyAllWindows()
	# 	pass

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


# class Camera_Setup_Handlers(Camera_Setup):

# 	def __init__( self, *args, parent=None, **kw):
# 		Camera_Setup.__init__ ( self, *args, **kw)
# 		graph = FilterGraph()
# 		self.parent = parent
# self.devices = graph.get_input_devices()
# 		self.cameras_list.Set(self.devices)
# 		self.cameras_list.SetValue(self.devices[0])
# 		self.res = {
# 			"640 x 480" : (640, 480),
# 			"800 x 600" : (1280, 720),
# 			"1280 x 720" : (1920, 1080),
# 			# "1920 x 1080" : (3840, 2160)
# 			"1920 x 1080" : (1920, 1440)
# 		}

# 	def on_cam_ok_btn(self, event):
# 		cam_name = self.cameras_list.GetValue()
# 		res = self.cameras_res.GetValue()
# 		for idx, val in enumerate(self.devices):
# 			if val == cam_name:
# 				wx.PostEvent(self.parent, UpdateCamera(idx, self.res[res]))


# 	def on_cam_cancel_btn(self, event):
# 		self.Destroy()

# 	def on_cam_set_close(self, event):
# 		self.Destroy()

# 	def __del__(self):
# 		pass
# class Measure_Menu_Handlers ( Measure_Menu ):

# 	def __init__( self, *args, **kw):
# 		Measure_Menu.__init__ ( self, *args, **kw)

# 		self.init_table()
# 		self.Bind(wx.EVT_CLOSE, self.on_close)

# 	def init_table(self):
# 		self.table_std.ClearGrid()
# 		self.path = os.path.join("data", "calibrations.csv")
# 		if os.path.exists(self.path):
# 			self.btn_chg_std.Enable(True)
# 			self.btn_rm_std.Enable(True)
# 			with open(self.path, mode ='r')as file:
# 				data = list(csv.reader(file))[1:]
# 			for row in range(len(data)):
# 				for col in range(len(data[row])):
# 					self.table_std.SetCellValue(row, col, data[row][col])
# 		else:
# 			self.btn_chg_std.Enable(False)
# 			self.btn_rm_std.Enable(False)


# 	def add_std(self, event):
# 		std_add_entry = Std_Entry_Add_Handlers(None, table_obj=self)
# 		std_add_entry.Show()

# 	def chg_std(self, event):
# 		std_chg_entry = Std_Entry_Chg_Handlers(None, table_obj=self)
# 		std_chg_entry.Show()

# 	def rm_std(self, event):
# 		std_rm_entry = Std_Entry_Rm_Handlers(None, table_obj=self)
# 		std_rm_entry.Show()

# 	def on_close(self, event):
# 		self.Destroy()

# 	def __del__(self):
# 		pass


# class Std_Entry_Add_Handlers(Std_Entry_Add):

# 	def __init__( self, *args, table_obj=None, **kw):
# 		Std_Entry_Add.__init__ ( self, *args, **kw)
# 		# self.path = os.path.join("data", "calibrations.csv")
# 		self.table_obj = table_obj
# 		self.path = self.table_obj.path

# 	def on_add_std_entry(self, event):
# 		name = self.std_name.GetValue()
# 		reflect = self.std_reflect.GetValue()

# 		if name != '' and reflect != "":
# 			if reflect.replace('.', '', 1).isdigit():
# 				with open(self.path, mode ='a') as file:
# 					file.write('\r{},{}'.format(name,float(reflect)))
# 				self.table_obj.init_table()
# 			else:
# 				wx.MessageBox("Не верно задан коэффициент отражения!", "ERROR", wx.OK | wx.ICON_ERROR)

# 	def on_add_cancel(self, event):
# 		self.Destroy()

# 	def on_add_close(self, event):
# 		self.Destroy()

# 	def __del__(self):
# 		pass

# class Std_Entry_Chg_Handlers(Std_Entry_Chg):

# 	def __init__( self, *args, table_obj=None, **kw):
# 		Std_Entry_Chg.__init__ ( self, *args, **kw)
# 		self.table_obj = table_obj
# 		self.path = self.table_obj.path
# 		self.data = None
# 		self.init_combo()

# 	def init_combo(self):
# 		if os.path.exists(self.path):
# 			with open(self.path, mode ='r')as file:
# 				self.data = dict(list(csv.reader(file))[1:])
# 			self.std_name2chg.Set(list(self.data.keys()))
# 			# for row in range(len(data)):
# 			# 	for col in range(len(data[row])):
# 			# 		self.table_std.SetCellValue(row, col, data[row][col])

# 	def on_chg_std_entry(self, event):
# 		name = self.std_name2chg.GetValue()
# 		reflect = self.std_reflect2chg.GetValue()

# 		if name != '' and reflect != "":
# 			if self.data != None:
# 				self.data[name] = reflect
# 				with open(self.path, mode ='w') as file:
# 					file.write('Name,Reflection')
# 					for key in self.data.keys():
# 						file.write('\r{},{}'.format(key,self.data[key]))
# 				self.table_obj.init_table()
# 				# self.Destroy()
# 		else:
# 			wx.MessageBox("Не верно задан коэффициент отражения!", "ERROR", wx.OK | wx.ICON_ERROR)

# 	def on_chg_close(self, event):
# 		self.Destroy()

# 	def on_chg_cancel(self, event):
# 		self.Destroy()

# 	def __del__(self):
# 		pass

# class Std_Entry_Rm_Handlers(Std_Entry_Rm):

# 	def __init__( self, *args, table_obj=None, **kw):
# 		Std_Entry_Rm.__init__ ( self, *args, **kw)
# 		self.table_obj = table_obj
# 		self.path = self.table_obj.path
# 		self.data = None
# 		self.init_combo()

# 	def init_combo(self):
# 		if os.path.exists(self.path):
# 			with open(self.path, mode ='r')as file:
# 				self.data = dict(list(csv.reader(file))[1:])
# 			self.std_name2rm.Set(list(self.data.keys()))

# 	def on_rm_std_entry(self, event):
# 		name = self.std_name2rm.GetValue()

# 		if self.data != None:
# 			self.data.pop(name)
# 			with open(self.path, mode ='w') as file:
# 				file.write('Name,Reflection')
# 				for key in self.data.keys():
# 					file.write('\r{},{}'.format(key,self.data[key]))

# 			self.table_obj.init_table()
# 			self.init_combo()

# 	def on_rm_close(self, event):
# 		self.Destroy()

# 	def on_rm_cancel(self, event):
# 		self.Destroy()

# 	def __del__(self):
# 		pass

# class Meas_Helper_Handlers(Meas_Helper):

# 	def __init__( self, *args, parent=None, **kw):
# 		Meas_Helper.__init__ ( self, *args, **kw)
# 		self.path = os.path.join("data", "calibrations.csv")
# 		self.data = None
# 		self.master = parent
# 		self.helper_std_table.Connect(-1, -1, EVT_ENOUGH_POINTS, self.on_f_next_btn)
# 		self.helper_std_table.Connect(-1, -1, EVT_NOT_ENOUGH_POINTS, self.off_f_next_btn)

# 		attr = grd.GridCellAttr()
# 		attr.SetEditor(grd.GridCellBoolEditor())
# 		attr.SetRenderer(grd.GridCellBoolRenderer())
# 		# self.helper_std_table.CreateGrid( 10, 3 )
# 		self.helper_std_table.SetColAttr(0,attr)
# 		self.helper_std_table.SetColSize(0,20)
# 		self.helper_std_table.SetColSize( 1, 165 )
# 		self.helper_std_table.SetColSize( 2, 165 )
# 		self.helper_std_table.EnableDragColMove( False )
# 		self.helper_std_table.EnableDragColSize( False )
# 		self.helper_std_table.EnableDragRowSize( False )
# 		self.helper_std_table.SetRowLabelSize( 0 )
# 		self.helper_std_table.SetColLabelValue( 1, u"Имя" )
# 		self.helper_std_table.SetColLabelValue( 2, u"Отражение [%]" )
# 		self.helper_std_table.SetColLabelValue( 0, wx.EmptyString )
# 		self.helper_std_table.SetColLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )
# 		self.helper_std_table.SetDefaultCellAlignment( wx.ALIGN_LEFT, wx.ALIGN_TOP )
# 		self.helper_std_table.SetRowLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )
# 		self.helper_std_table.SetMinSize( wx.Size( 350,200 ) )
# 		self.helper_std_table.SetMaxSize( wx.Size( 350,200 ) )

# 		self.init_combo()

# 	def init_combo(self):
# 		if os.path.exists(self.path):
# 			with open(self.path, mode ='r')as file:
# 				self.data = list(csv.reader(file))[1:]
# 			print(self.data)
# 			for row in range(len(self.data)):
# 				for col in range(len(self.data[row])):
# 					self.helper_std_table.SetCellValue(row, col+1, self.data[row][col])

# 	def on_helper_cancel_btn(self, event):
# 		self.Destroy()
# 		pass

# 	def on_f_next_btn(self, event):
# 		self.samples = []
# 		for value in event.values:
# 			self.samples.append(self.data[int(value)])
# 		# print("Sanples: ", samples)
# 		self.helper_f_next_btn.Enable()

# 	def off_f_next_btn(self, event):
# 		self.helper_f_next_btn.Disable()

# 	def on_helper_f_next_btn(self, event):
# 		cal = Meas_Helper_Cal_Handlers(None, parent=self)
# 		cal.Show()
# 		self.Hide()

# 	def on_close_helper(self, event):
# 		self.Destroy()

# 	def __del__(self):
# 		pass


# class Meas_Helper_Cal_Handlers(Meas_Helper_Cal):
# 	def __init__( self, *args, parent = None, **kw):
# 		Meas_Helper_Cal.__init__ ( self, *args, **kw)
# 		self.parent = parent
# 		self.samples_names = []
# 		self.samples_refl = []
# 		self.samples_intens = []
# 		self.samples_nmeas = []
# 		self.samples_btn_meas = []
# 		self.samples_btn_cancel = []
# 		self.id_idx_dict = dict()

# 		self.current_meas_idx = None
# 		self.current_meas_table = dict()

# 		self.ghost1.Hide()
# 		self.ghost2.Hide()
# 		self.ghost3.Hide()
# 		self.ghost4.Hide()
# 		self.btn_ghost1.Hide()
# 		self.btn_ghost2.Hide()

# 		self.helper_s_next_btn.Disable()

# 		self.parent.master.Connect(-1, -1, EVT_CALIBRATION, self.on_cal_update)

# 		for idx, val in enumerate(self.parent.samples):
# 			self.samples_names.append(wx.StaticText( self, wx.ID_ANY, self.parent.samples[idx][0], wx.DefaultPosition, wx.DefaultSize, 0 ))
# 			self.samples_names[idx].Wrap( -1 )
# 			self.name_sizer.Add( self.samples_names[idx], 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

# 			self.samples_refl.append(wx.StaticText( self, wx.ID_ANY, str(self.parent.samples[idx][1]), wx.DefaultPosition, wx.DefaultSize, 0 ))
# 			self.samples_refl[idx].Wrap( -1 )
# 			self.refl_sizer.Add( self.samples_refl[idx], 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

# 			self.samples_intens.append(wx.StaticText( self, wx.ID_ANY, str(0), wx.DefaultPosition, wx.DefaultSize, 0 ))
# 			self.samples_intens[idx].Wrap( -1 )
# 			self.intens_sizer.Add( self.samples_intens[idx], 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

# 			self.samples_nmeas.append(wx.StaticText( self, wx.ID_ANY, str(0), wx.DefaultPosition, wx.DefaultSize, 0 ))
# 			self.samples_nmeas[idx].Wrap( -1 )
# 			self.nmeas_sizer.Add( self.samples_nmeas[idx], 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

# 			self.samples_btn_meas.append( wx.Button( self, wx.ID_ANY, u"Измерить", wx.DefaultPosition, wx.DefaultSize, 0 ))
# 			self.btn_meas_sizer.Add( self.samples_btn_meas[idx], 0, wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM, 5 )
# 			self.samples_btn_meas[idx].Bind( wx.EVT_BUTTON, self.on_btn_meas )
# 			self.id_idx_dict[str(self.samples_btn_meas[idx].Id)] = idx

# 			self.samples_btn_cancel.append( wx.Button( self, wx.ID_ANY, u"Сброс", wx.DefaultPosition, wx.DefaultSize, 0 ))
# 			self.btn_cancel_sizer.Add( self.samples_btn_cancel[idx], 0, wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM, 5 )
# 			self.samples_btn_cancel[idx].Bind( wx.EVT_BUTTON, self.on_btn_cancel )
# 			self.id_idx_dict[str( self.samples_btn_cancel[idx].Id)] = idx

# 			# self.id_idx_dict[str(idx)] = [self.samples_btn_meas[idx].Id, self.samples_btn_cancel[idx].Id]

# 		self.SetSizer( self.fgSizer9 )
# 		self.Layout()

# 	def on_btn_meas(self, event):
# 		self.current_meas_idx = self.id_idx_dict[str(event.Id)]
# 		try:
# 			if len(self.current_meas_table[str(self.current_meas_idx)]) > 0:
# 				pass
# 		except:
# 			self.current_meas_table[str(self.current_meas_idx)] = []
# 		self.parent.master.panel_cam_img.meas_on = True

# 	def on_btn_cancel(self, event):
# 		idx = self.id_idx_dict[str(event.Id)]
# 		self.current_meas_table[str(idx)] = []
# 		self.samples_intens[idx].SetLabel("0")
# 		self.samples_nmeas[idx].SetLabel("0")

# 		self.check_meas_ready()

# 	def on_helper_s_back_btn(self, event):
# 		self.parent.master.panel_cam_img.meas_on = False
# 		self.parent.Show()
# 		self.Destroy()

# 	def on_helper_s_next_btn(self, event):
# 		self.parent.master.panel_cam_img.meas_on = False
# 		data = []
# 		for idx, value in enumerate(self.samples_names):
# 			data.append([value.GetLabel(), self.samples_refl[idx].GetLabel(), self.current_meas_table[str(idx)]])
# 		cal = Meas_Helper_Last_Handlers(None, parent=self, data = data)
# 		cal.Show()
# 		self.Hide()

# 	def on_cal_update(self, event):
# 		val = event.value
# 		self.current_meas_table[str(self.current_meas_idx)].append(val)
# 		self.samples_intens[self.current_meas_idx].SetLabel("{:.2f}".format(val))
# 		self.samples_nmeas[self.current_meas_idx].SetLabel(str(len(self.current_meas_table[str(self.current_meas_idx)])))

# 		self.check_meas_ready()


# 	def check_meas_ready(self):
# 		try:
# 			k = 0
# 			for idx, val in enumerate(self.samples_nmeas):
# 				if int(self.samples_nmeas[idx].GetLabel()) != 0:
# 					k += 1
# 			if k == len(self.samples_nmeas):
# 				self.helper_s_next_btn.Enable()
# 			else:
# 				self.helper_s_next_btn.Disable()
# 		except:
# 			pass


# 	def on_close(self, event):
# 		self.parent.master.panel_cam_img.meas_on = False
# 		self.Destroy()
# 		self.parent.Destroy()

# 	def on_helper_cancel_btn(self, event):
# 		self.parent.master.panel_cam_img.meas_on = False
# 		self.Destroy()
# 		self.parent.Destroy()

# 	def __del__(self):
# 		pass


# class Meas_Helper_Last_Handlers(Meas_Helper_Cal):
# 	def __init__( self, *args, parent = None, data=None, **kw):
# 		Meas_Helper_Last.__init__ ( self, *args, **kw)
# 		self.data = data
# 		self.parent = parent

# 		x = []
# 		y = []

# 		for each in data:
# 			y.append(float(each[1]))
# 			x.append(np.sum(each[2])/len(each[2]))

# 		degree = len(x)-2

# 		x = np.array(x)
# 		y = np.array(y)

# 		# Define the degree of the polynomial

# 		print("degree: ", degree)

# 		self.fit = np.poly1d(np.polyfit(x, y, degree))

# 		x_fit = np.linspace(0, 255, 256)
# 		print("X_fit: ", x_fit)
# 		y_fit = self.fit(x_fit)
# 		print("Y_fit: ", y_fit)

# 		# self.figure = Figure()
# 		# self.axes = self.figure.add_subplot()
# 		self.figure_panel.axes.plot(x_fit, y_fit)
# 		self.figure_panel.axes.scatter(x, y, s=4)
# 		# self.figure_panel.axes.set_title("Wafer" + " " + os.path.basename(os.path.normpath(path)))
# 		self.figure_panel.axes.grid(which="major", color="#AAAAAA", linewidth=0.8)
# 		self.figure_panel.axes.grid(which="minor", color="#DDDDDD", linestyle=":", linewidth=0.5)
# 		self.figure_panel.axes.minorticks_on()
# 		self.figure_panel.axes.set_ylabel(r"Отражение [%]", fontsize=10)
# 		self.figure_panel.axes.set_xlabel(r"Интенсивность", fontsize=10)


# 	# Virtual event handlers, override them in your derived class
# 	def on_helper_thr_back_btn( self, event ):
# 		self.parent.Show()
# 		self.Destroy()

# 	def on_helper_thr_next_btn( self, event ):
# 		n_meas = int(self.n_meas.GetValue())
# 		self.parent.parent.master.on_run_meas_init(n_meas, self.fit)

# 		self.parent.parent.master.panel_cam_img.meas_on = False
# 		self.parent.Destroy()
# 		self.parent.parent.Destroy()
# 		self.Destroy()

# 	def on_helper_thr_cancel_btn( self, event ):
# 		self.parent.parent.master.panel_cam_img.meas_on = False
# 		self.parent.Destroy()
# 		self.parent.parent.Destroy()
# 		self.Destroy()

# 	def __del__( self ):
# 		pass

# class Lens_Setup_Handlers ( Lens_Setup ):

# 	def __init__( self, *args, parent = None, **kw):
# 		Lens_Setup.__init__ ( self, *args, **kw)

# 		self.data_lens = [[],[]]
# 		self.parent = parent
# 		self.path_lens = os.path.join("data", "lenses.csv")
# 		self.init_table()
# 		self.Bind(wx.EVT_CLOSE, self.on_close)
# 		self.lens_stp_table.SetSelectionMode(wx.grid.Grid.GridSelectRows)


# 	class Lens_Add_Cal_Handlers ( Lens_Add_Cal ):
# 		def __init__( self, *args, value = None, parent = None, **kw):
# 			Lens_Add_Cal.__init__ ( self, *args, **kw)

# 			if value is not None:
# 				self.length_pxl.SetValue(str(value))

# 			self.post_event_to = parent.parent.panel_cam_img
# 			self. parent = parent


# 		def on_lens_cal_repeat( self, event ):
# 			if self.post_event_to is not None:
# 				wx.PostEvent(self.post_event_to, OnLensCalibrationInit(1))
# 			self.Destroy()

# 		def on_lens_cal_add( self, event ):
# 			length_meters = self.length_meters.GetValue()
# 			if length_meters != '':
# 				if length_meters.replace('.', '', 1).isdigit():
# 					length_pxl = self.length_pxl.GetValue()
# 					if length_pxl is not None:
# 						self.parent.lens_stp_cal.SetValue("{:.3f}".format((float(length_meters)/int(length_pxl))))
# 						self.parent.lens_stp_chbx.SetSelection(self.length_units.GetSelection())
# 						self.parent.Show()
# 						wx.PostEvent(self.post_event_to, OnLensCalibrationStop(1))
# 				self.Destroy()
# 			else:
# 				wx.MessageBox("Введите расстояние!", "ERROR", wx.OK | wx.ICON_ERROR)

# 		def __del__( self ):
# 		# Disconnect Events
# 			pass

# 		def on_close(self, event):
# 			wx.PostEvent(self.post_event_to, OnLensCalibrationStop(1))
# 			self.Destroy()

# 	def init_table(self):
# 		self.lens_stp_table.ClearGrid()
# 		if os.path.exists(self.path_lens):
# 			with open(self.path_lens, mode ='r')as file:
# 				self.data_lens = list(csv.reader(file))[1:]

# 			delta = int(len(self.data_lens) - self.lens_stp_table.GetNumberRows())
# 			if delta > 0:
# 				self.lens_stp_table.AppendRows(delta+3)

# 			for row in range(len(self.data_lens)):
# 				for col in range(len(self.data_lens[row])):
# 					self.lens_stp_table.SetCellValue(row, col, self.data_lens[row][col])
# 		else:
# 			wx.MessageBox("Отсутствует список объективов!", "ИНФОРМАЦИЯ", wx.OK | wx.ICON_INFORMATION)

# 	def on_grid_lclick( self, event ):
# 		# print(event.Col, event.Row)
# 		# print(self.lens_stp_table.GetCellValue(event.Row, event.Col))

# 		try:
# 			name = self.lens_stp_table.GetCellValue(event.Row, 0)
# 			cal, units, *_ = self.lens_stp_table.GetCellValue(event.Row, 1).split(" ")
# 		except ValueError:
# 				name = ""
# 				cal = ""
# 				units = ""

# 		print(cal, units)
# 		self.lens_stp_name.SetValue(name)
# 		self.lens_stp_cal.SetValue(cal)
# 		self.lens_stp_chbx.SetSelection(1) if units == 'mm/px' else self.lens_stp_chbx.SetSelection(0)

# 		if name != "":
# 			self.lens_stp_chbx.Disable()
# 			self.lens_stp_cal_btn.Disable()
# 			self.lens_stp_add_btn.Disable()
# 		else:
# 			self.lens_stp_chbx.Enable()
# 			self.lens_stp_cal_btn.Enable()
# 			self.lens_stp_add_btn.Enable()
# 		# self.lens_stp_cals.SetValue()


# 	def on_lens_stp_chbx( self, event ):
# 		event.Skip()

# 	def on_lens_stp_cal_btn( self, event ):
# 		self.Hide()
# 		wx.MessageBox("Проведите калибровочный отрезок на изображении", "ИНФОРМАЦИЯ", wx.OK | wx.ICON_INFORMATION)
# 		if self.parent is not None:
# 			self.parent.panel_cam_img.Connect(-1, -1, EVT_LENS_CALIBRATION, self.on_get_lens_cal)
# 			wx.PostEvent(self.parent.panel_cam_img, OnLensCalibrationInit(1))


# 	def on_get_lens_cal(self, event):
# 		print(event.value)
# 		add = self.Lens_Add_Cal_Handlers(None, value = event.value, parent = self)
# 		add.Show()
# 		# self.Show()
# 		# self.Disconnect()

# 	def on_lens_stp_add_btn( self, event ):
# 		try:
# 			name = self.lens_stp_name.GetValue()
# 		except ValueError:
# 			name = ""

# 		try:
# 			cal = self.lens_stp_cal.GetValue()
# 		except ValueError:
# 			cal = ""

# 		try:
# 			units = self.lens_stp_chbx.GetString(self.lens_stp_chbx.GetSelection())
# 		except ValueError:
# 			units = ""

# 		print(name, cal)
# 		if name != "" and cal != "":
# 			if cal.replace('.', '', 1).isdigit():
# 				with open(self.path_lens, mode ='a') as file:
# 					file.write('\r{},{} {} @ {}'.format(name,float(cal), units, "test resolution"))
# 				self.init_table()
# 			else:
# 				wx.MessageBox("Не верно задана калибровка!", "ERROR", wx.OK | wx.ICON_ERROR)

# 	def on_lens_stp_del_btn( self, event ):
# 		try:
# 			name = self.lens_stp_name.GetValue()
# 		except ValueError:
# 			name = ""

# 		if name != "":
# 			data_dict = dict(self.data_lens)
# 			print(data_dict)
# 			data_dict.pop(name)
# 			with open(self.path_lens, mode ='w') as file:
# 				file.write('Name,Calibration')
# 				for key in data_dict:
# 					# print()"Key"
# 					file.write('\r{},{}'.format(key, data_dict[key]))

# 			self.init_table()

# 	def on_lens_stp_cancel_btn( self, event ):
# 		wx.PostEvent(self.parent.panel_cam_img, OnLensCalibrationStop(1))
# 		self.Destroy()

# 	def on_close(self, event):
# 		wx.PostEvent(self.parent.panel_cam_img, OnLensCalibrationStop(1))
# 		self.Destroy()

# 	def __del__(self):
# 		pass

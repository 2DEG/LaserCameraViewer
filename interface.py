# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-0-g8feb16b3)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

from video_view import VideoView
import wx
import wx.xrc

###########################################################################
## Class Main_Frame
###########################################################################

class Main_Frame ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 988,697 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		self.menu_toolbar = self.CreateToolBar( wx.TB_HORIZONTAL, wx.ID_ANY )
		self.t_start = self.menu_toolbar.AddTool( wx.ID_ANY, u"Start", wx.Bitmap( u"icons/24px/003-play-button.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, u"Start acquisition", wx.EmptyString, None )

		self.t_stop = self.menu_toolbar.AddTool( wx.ID_ANY, u"Stop", wx.Bitmap( u"icons/24px/005-stop.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, u"Stop acquisition", wx.EmptyString, None )

		self.menu_toolbar.AddSeparator()

		self.menu_toolbar.AddSeparator()

		self.t_scr_sht = self.menu_toolbar.AddTool( wx.ID_ANY, u"Screenshot", wx.Bitmap( u"icons/24px/007-camera.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, u"Single shot", wx.EmptyString, None )

		self.t_vid = self.menu_toolbar.AddTool( wx.ID_ANY, u"Video", wx.Bitmap( u"icons/24px/002-camera.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_CHECK, u"Start/Stop recording", wx.EmptyString, None )

		self.menu_toolbar.AddSeparator()

		self.menu_toolbar.AddSeparator()

		self.t_track = self.menu_toolbar.AddTool( wx.ID_ANY, u"Track", wx.Bitmap( u"icons/24px/001-epicenter.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_CHECK, u"Start/Stop tracking", wx.EmptyString, None )

		self.menu_toolbar.Realize()

		self.m_menubar1 = wx.MenuBar( 0 )
		self.file_menu = wx.Menu()
		self.m_menubar1.Append( self.file_menu, u"File" )

		self.camera_menu = wx.Menu()
		self.opt_camera_menu = wx.MenuItem( self.camera_menu, wx.ID_ANY, u"Options", wx.EmptyString, wx.ITEM_NORMAL )
		self.camera_menu.Append( self.opt_camera_menu )

		self.m_menubar1.Append( self.camera_menu, u"Camera" )

		self.help_menu = wx.Menu()
		self.m_menubar1.Append( self.help_menu, u"Help" )

		self.SetMenuBar( self.m_menubar1 )

		fgSizer1 = wx.FlexGridSizer( 0, 2, 0, 0 )
		fgSizer1.AddGrowableCol( 0, 3 )
		fgSizer1.AddGrowableCol( 1, 1 )
		fgSizer1.AddGrowableRow( 0, 1 )
		fgSizer1.SetFlexibleDirection( wx.BOTH )
		fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.panel_cam = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		self.panel_cam_img = VideoView( self.panel_cam, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer1.Add( self.panel_cam_img, 1, wx.EXPAND |wx.ALL, 5 )


		self.panel_cam.SetSizer( bSizer1 )
		self.panel_cam.Layout()
		bSizer1.Fit( self.panel_cam )
		fgSizer1.Add( self.panel_cam, 1, wx.EXPAND |wx.ALL, 5 )

		bSizer131 = wx.BoxSizer( wx.VERTICAL )

		self.notebook = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		self.n_settings = wx.Panel( self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.Size( 10,-1 ), wx.TAB_TRAVERSAL )
		self.n_settings.SetMinSize( wx.Size( 10,-1 ) )
		self.n_settings.SetMaxSize( wx.Size( 10,-1 ) )

		fgSizer2 = wx.FlexGridSizer( 8, 0, 0, 0 )
		fgSizer2.AddGrowableCol( 0, 1 )
		fgSizer2.AddGrowableRow( 0, 1 )
		fgSizer2.AddGrowableRow( 1, 1 )
		fgSizer2.AddGrowableRow( 2, 1 )
		fgSizer2.AddGrowableRow( 3, 1 )
		fgSizer2.AddGrowableRow( 4, 1 )
		fgSizer2.AddGrowableRow( 5, 1 )
		fgSizer2.AddGrowableRow( 6, 1 )
		fgSizer2.AddGrowableRow( 7, 20 )
		fgSizer2.SetFlexibleDirection( wx.BOTH )
		fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.m_staticText1 = wx.StaticText( self.n_settings, wx.ID_ANY, u"Exposure time:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )

		fgSizer2.Add( self.m_staticText1, 0, wx.ALL, 5 )

		bSizer14 = wx.BoxSizer( wx.HORIZONTAL )

		self.exp_slider = wx.Slider( self.n_settings, wx.ID_ANY, 500000, 1, 1000000, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL|wx.SL_MIN_MAX_LABELS|wx.SL_VALUE_LABEL )
		bSizer14.Add( self.exp_slider, 1, wx.ALL|wx.ALIGN_BOTTOM, 5 )

		self.exp_text = wx.SpinCtrlDouble( self.n_settings, wx.ID_ANY, u"500000", wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 1, 1e+06, 499998.000000, 1 )
		self.exp_text.SetDigits( 0 )
		bSizer14.Add( self.exp_text, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		fgSizer2.Add( bSizer14, 1, wx.EXPAND, 5 )

		self.m_staticText2 = wx.StaticText( self.n_settings, wx.ID_ANY, u"Gain:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )

		fgSizer2.Add( self.m_staticText2, 0, wx.ALL, 5 )

		bSizer13 = wx.BoxSizer( wx.HORIZONTAL )

		self.gain_slider = wx.Slider( self.n_settings, wx.ID_ANY, 16, 1, 32, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL|wx.SL_MIN_MAX_LABELS|wx.SL_VALUE_LABEL )
		bSizer13.Add( self.gain_slider, 1, wx.ALL|wx.ALIGN_BOTTOM, 5 )

		self.gain_text = wx.SpinCtrlDouble( self.n_settings, wx.ID_ANY, u"16", wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 1, 32, 1.000000, 1 )
		self.gain_text.SetDigits( 0 )
		bSizer13.Add( self.gain_text, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		fgSizer2.Add( bSizer13, 1, wx.EXPAND, 5 )

		bSizer3 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText3 = wx.StaticText( self.n_settings, wx.ID_ANY, u"FPS:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )

		bSizer3.Add( self.m_staticText3, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.fps_text = wx.SpinCtrlDouble( self.n_settings, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 60, 30, 0.001 )
		self.fps_text.SetDigits( 3 )
		bSizer3.Add( self.fps_text, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		fgSizer2.Add( bSizer3, 1, wx.EXPAND, 5 )

		bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText4 = wx.StaticText( self.n_settings, wx.ID_ANY, u"Bit depth:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )

		self.m_staticText4.Hide()

		bSizer4.Add( self.m_staticText4, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		bit_choiceChoices = [ u"4", u"8" ]
		self.bit_choice = wx.Choice( self.n_settings, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, bit_choiceChoices, 0 )
		self.bit_choice.SetSelection( 0 )
		self.bit_choice.Hide()

		bSizer4.Add( self.bit_choice, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		fgSizer2.Add( bSizer4, 1, wx.EXPAND, 5 )

		self.rgb_choice = wx.CheckBox( self.n_settings, wx.ID_ANY, u"RGB mode ON", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.rgb_choice.Hide()

		fgSizer2.Add( self.rgb_choice, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

		self.m_panel6 = wx.Panel( self.n_settings, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		fgSizer2.Add( self.m_panel6, 1, wx.EXPAND |wx.ALL, 5 )


		self.n_settings.SetSizer( fgSizer2 )
		self.n_settings.Layout()
		self.notebook.AddPage( self.n_settings, u"Settings", False )
		self.n_stab_track = wx.Panel( self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.Size( 10,-1 ), wx.TAB_TRAVERSAL )
		self.n_stab_track.SetMinSize( wx.Size( 10,-1 ) )
		self.n_stab_track.SetMaxSize( wx.Size( 10,-1 ) )

		fgSizer3 = wx.FlexGridSizer( 5, 0, 0, 0 )
		fgSizer3.AddGrowableCol( 0, 1 )
		fgSizer3.AddGrowableRow( 0, 1 )
		fgSizer3.AddGrowableRow( 1, 1 )
		fgSizer3.AddGrowableRow( 2, 1 )
		fgSizer3.AddGrowableRow( 3, 1 )
		fgSizer3.AddGrowableRow( 4, 20 )
		fgSizer3.SetFlexibleDirection( wx.BOTH )
		fgSizer3.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		bSizer5 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText5 = wx.StaticText( self.n_stab_track, wx.ID_ANY, u"Fix beam pos.: (x, y)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )

		bSizer5.Add( self.m_staticText5, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_button2 = wx.Button( self.n_stab_track, wx.ID_ANY, u"Apply", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer5.Add( self.m_button2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		fgSizer3.Add( bSizer5, 1, wx.EXPAND, 5 )

		bSizer7 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText6 = wx.StaticText( self.n_stab_track, wx.ID_ANY, u"Time period (bin size) in (s): ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )

		bSizer7.Add( self.m_staticText6, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.time_bin = wx.SpinCtrlDouble( self.n_stab_track, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 1e+07, 1, 1 )
		self.time_bin.SetDigits( 0 )
		bSizer7.Add( self.time_bin, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		fgSizer3.Add( bSizer7, 1, wx.EXPAND, 5 )

		bSizer9 = wx.BoxSizer( wx.VERTICAL )

		bSizer121 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText11 = wx.StaticText( self.n_stab_track, wx.ID_ANY, u"Cross's line length in (px):", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )

		bSizer121.Add( self.m_staticText11, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.line_len = wx.SpinCtrlDouble( self.n_stab_track, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 1000, 100, 1 )
		self.line_len.SetDigits( 0 )
		bSizer121.Add( self.line_len, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		bSizer9.Add( bSizer121, 1, wx.EXPAND, 5 )

		self.m_staticText7 = wx.StaticText( self.n_stab_track, wx.ID_ANY, u"Save track to:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )

		bSizer9.Add( self.m_staticText7, 0, wx.ALL, 5 )

		self.m_dirPicker21 = wx.DirPickerCtrl( self.n_stab_track, wx.ID_ANY, wx.EmptyString, u"Select a folder", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE )
		bSizer9.Add( self.m_dirPicker21, 0, wx.ALL|wx.EXPAND, 5 )


		fgSizer3.Add( bSizer9, 1, wx.EXPAND, 5 )

		self.m_checkBox2 = wx.CheckBox( self.n_stab_track, wx.ID_ANY, u"Show/Hide tracking", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer3.Add( self.m_checkBox2, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

		self.m_panel8 = wx.Panel( self.n_stab_track, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		fgSizer3.Add( self.m_panel8, 1, wx.EXPAND |wx.ALL, 5 )


		self.n_stab_track.SetSizer( fgSizer3 )
		self.n_stab_track.Layout()
		self.notebook.AddPage( self.n_stab_track, u"Stability Tracking", True )
		self.n_rec = wx.Panel( self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.Size( 10,-1 ), wx.TAB_TRAVERSAL )
		self.n_rec.SetMinSize( wx.Size( 10,-1 ) )
		self.n_rec.SetMaxSize( wx.Size( 10,-1 ) )

		fgSizer4 = wx.FlexGridSizer( 4, 0, 0, 0 )
		fgSizer4.AddGrowableCol( 0, 1 )
		fgSizer4.AddGrowableRow( 0, 1 )
		fgSizer4.AddGrowableRow( 1, 1 )
		fgSizer4.AddGrowableRow( 2, 1 )
		fgSizer4.AddGrowableRow( 3, 100 )
		fgSizer4.SetFlexibleDirection( wx.BOTH )
		fgSizer4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		bSizer12 = wx.BoxSizer( wx.VERTICAL )

		self.m_texttext = wx.StaticText( self.n_rec, wx.ID_ANY, u"Save records to:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_texttext.Wrap( -1 )

		bSizer12.Add( self.m_texttext, 0, wx.ALL, 5 )

		self.m_dirPicker2 = wx.DirPickerCtrl( self.n_rec, wx.ID_ANY, wx.EmptyString, u"Select a folder", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE )
		bSizer12.Add( self.m_dirPicker2, 0, wx.ALL|wx.EXPAND, 5 )


		fgSizer4.Add( bSizer12, 1, wx.EXPAND, 5 )

		self.m_staticText9 = wx.StaticText( self.n_rec, wx.ID_ANY, u"Screenshots sequence options:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText9.Wrap( -1 )

		fgSizer4.Add( self.m_staticText9, 0, wx.ALL, 5 )

		bSizer11 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText10 = wx.StaticText( self.n_rec, wx.ID_ANY, u"Record time period in (ms):", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText10.Wrap( -1 )

		bSizer11.Add( self.m_staticText10, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.video_rate = wx.SpinCtrl( self.n_rec, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 100, 1000000, 0 )
		bSizer11.Add( self.video_rate, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		fgSizer4.Add( bSizer11, 1, wx.EXPAND, 5 )

		self.m_panel9 = wx.Panel( self.n_rec, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		fgSizer4.Add( self.m_panel9, 1, wx.EXPAND |wx.ALL, 5 )


		self.n_rec.SetSizer( fgSizer4 )
		self.n_rec.Layout()
		self.notebook.AddPage( self.n_rec, u"Rec.", False )

		bSizer131.Add( self.notebook, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText12 = wx.StaticText( self, wx.ID_ANY, u"Info Monitor:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12.Wrap( -1 )

		bSizer131.Add( self.m_staticText12, 0, wx.ALL, 5 )

		self.info_monitor = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_RICH )
		bSizer131.Add( self.info_monitor, 1, wx.ALL|wx.EXPAND, 5 )


		fgSizer1.Add( bSizer131, 1, wx.EXPAND, 5 )


		self.SetSizer( fgSizer1 )
		self.Layout()
		self.statusbar = self.CreateStatusBar( 6, wx.STB_SIZEGRIP, wx.ID_ANY )

		self.Centre( wx.BOTH )

		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.on_close )
		self.Bind( wx.EVT_TOOL, self.on_acq_start, id = self.t_start.GetId() )
		self.Bind( wx.EVT_TOOL, self.on_acq_stop, id = self.t_stop.GetId() )
		self.Bind( wx.EVT_TOOL, self.on_screenshot, id = self.t_scr_sht.GetId() )
		self.Bind( wx.EVT_TOOL, self.on_rec_start_stop, id = self.t_vid.GetId() )
		self.Bind( wx.EVT_TOOL, self.on_tracking_start_stop, id = self.t_track.GetId() )
		self.Bind( wx.EVT_MENU, self.opt_cam_start, id = self.opt_camera_menu.GetId() )
		self.panel_cam_img.Bind( wx.EVT_ENTER_WINDOW, self.on_enter_cam_panel )
		self.panel_cam_img.Bind( wx.EVT_LEFT_DCLICK, self.on_mouse_click )
		self.exp_slider.Bind( wx.EVT_SLIDER, self.on_exp_slider )
		self.exp_text.Bind( wx.EVT_SPINCTRLDOUBLE, self.on_exp_enter )
		self.gain_slider.Bind( wx.EVT_SLIDER, self.on_gain_slider )
		self.gain_text.Bind( wx.EVT_SPINCTRLDOUBLE, self.on_gain_enter )
		self.fps_text.Bind( wx.EVT_SPINCTRLDOUBLE, self.on_fps_enter )
		self.fps_text.Bind( wx.EVT_TEXT, self.on_fps_enter )
		self.fps_text.Bind( wx.EVT_TEXT_ENTER, self.on_fps_enter )
		self.bit_choice.Bind( wx.EVT_CHOICE, self.on_bit_choice )
		self.rgb_choice.Bind( wx.EVT_CHECKBOX, self.on_rgb_choice )
		self.m_button2.Bind( wx.EVT_BUTTON, self.on_tracking_appl )
		self.time_bin.Bind( wx.EVT_SPINCTRLDOUBLE, self.on_timebin_text )
		self.time_bin.Bind( wx.EVT_TEXT_ENTER, self.on_timebin_text )
		self.line_len.Bind( wx.EVT_SPINCTRLDOUBLE, self.on_line_len_text )
		self.line_len.Bind( wx.EVT_TEXT_ENTER, self.on_line_len_text )
		self.m_dirPicker21.Bind( wx.EVT_DIRPICKER_CHANGED, self.on_track_saving_dir )
		self.m_checkBox2.Bind( wx.EVT_CHECKBOX, self.on_show_hide )
		self.m_dirPicker2.Bind( wx.EVT_DIRPICKER_CHANGED, self.on_rec_dir )
		self.video_rate.Bind( wx.EVT_SPINCTRL, self.on_video_rate )

	def __del__( self ):
		pass


	# Virtual event handlers, override them in your derived class
	def on_close( self, event ):
		event.Skip()

	def on_acq_start( self, event ):
		event.Skip()

	def on_acq_stop( self, event ):
		event.Skip()

	def on_screenshot( self, event ):
		event.Skip()

	def on_rec_start_stop( self, event ):
		event.Skip()

	def on_tracking_start_stop( self, event ):
		event.Skip()

	def opt_cam_start( self, event ):
		event.Skip()

	def on_enter_cam_panel( self, event ):
		event.Skip()

	def on_mouse_click( self, event ):
		event.Skip()

	def on_exp_slider( self, event ):
		event.Skip()

	def on_exp_enter( self, event ):
		event.Skip()

	def on_gain_slider( self, event ):
		event.Skip()

	def on_gain_enter( self, event ):
		event.Skip()

	def on_fps_enter( self, event ):
		event.Skip()



	def on_bit_choice( self, event ):
		event.Skip()

	def on_rgb_choice( self, event ):
		event.Skip()

	def on_tracking_appl( self, event ):
		event.Skip()

	def on_timebin_text( self, event ):
		event.Skip()


	def on_line_len_text( self, event ):
		event.Skip()


	def on_track_saving_dir( self, event ):
		event.Skip()

	def on_show_hide( self, event ):
		event.Skip()

	def on_rec_dir( self, event ):
		event.Skip()

	def on_video_rate( self, event ):
		event.Skip()


###########################################################################
## Class Camera_Options_Frame
###########################################################################

class Camera_Options_Frame ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Camera setup", pos = wx.DefaultPosition, size = wx.Size( 300,200 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.Size( 300,200 ), wx.Size( 300,200 ) )

		bSizer13 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText13 = wx.StaticText( self, wx.ID_ANY, u"List of available cameras:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText13.Wrap( -1 )

		bSizer13.Add( self.m_staticText13, 0, wx.ALL, 5 )

		cameras_listChoices = []
		self.cameras_list = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, cameras_listChoices, 0 )
		self.cameras_list.SetSelection( 0 )
		bSizer13.Add( self.cameras_list, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText14 = wx.StaticText( self, wx.ID_ANY, u"Cameras backend:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText14.Wrap( -1 )

		bSizer13.Add( self.m_staticText14, 0, wx.ALL, 5 )

		backends_listChoices = [ u"MV Viewer (Dahua)", u"OpenCV (DShow)", u"VimbaX" ]
		self.backends_list = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, backends_listChoices, 0 )
		self.backends_list.SetSelection( 0 )
		bSizer13.Add( self.backends_list, 0, wx.ALL|wx.EXPAND, 5 )

		bSizer14 = wx.BoxSizer( wx.HORIZONTAL )


		bSizer14.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_button2 = wx.Button( self, wx.ID_ANY, u"Apply", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer14.Add( self.m_button2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_button3 = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer14.Add( self.m_button3, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		bSizer13.Add( bSizer14, 1, wx.EXPAND, 5 )


		self.SetSizer( bSizer13 )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.on_close )
		self.cameras_list.Bind( wx.EVT_CHOICE, self.on_camera_ch )
		self.backends_list.Bind( wx.EVT_CHOICE, self.on_backend_ch )
		self.m_button2.Bind( wx.EVT_BUTTON, self.on_apply )
		self.m_button3.Bind( wx.EVT_BUTTON, self.on_cancel )

	def __del__( self ):
		pass


	# Virtual event handlers, override them in your derived class
	def on_close( self, event ):
		event.Skip()

	def on_camera_ch( self, event ):
		event.Skip()

	def on_backend_ch( self, event ):
		event.Skip()

	def on_apply( self, event ):
		event.Skip()

	def on_cancel( self, event ):
		event.Skip()



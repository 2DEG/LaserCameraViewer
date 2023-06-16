from interface.gui_handlers import Frame_Handlers
import wx


class MyApp(wx.App):
    """Main application class."""

    def __init__(self):
        super().__init__(clearSigInt=True)

        self.mainFrame = Frame_Handlers(None)
        self.mainFrame.Show()


if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
    wx.Exit()

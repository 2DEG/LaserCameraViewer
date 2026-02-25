import logging
import os
from datetime import datetime

import wx

# ---------------------------------------------------------------------------
# Logging setup: console + file in logs/ directory
# ---------------------------------------------------------------------------
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(
    LOG_DIR, datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
)

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)
logger.info("Log file: %s", LOG_FILE)

# ---------------------------------------------------------------------------
from interface.gui_handlers import Frame_Handlers


class MyApp(wx.App):
    """Main application class."""

    def __init__(self):
        super().__init__(clearSigInt=True)

        self.mainFrame = Frame_Handlers(None)
        self.mainFrame.Show()


if __name__ == "__main__":
    try:
        logger.info("Starting LaserCameraViewer")
        app = MyApp()
        app.MainLoop()
    except Exception:
        logger.exception("Unhandled exception — application crashed")
    finally:
        logger.info("Application exiting")
        logging.shutdown()
        wx.Exit()

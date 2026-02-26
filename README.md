# Beam Alignment System

Beam Alignment System is an open-source Python application for real-time video processing. This system can detect ellipses in video frames, which is useful for laser beam alignment and stability tracking.

## Features

- Real-time video processing
- Ellipse (laser beam) detection in video frames with configurable parameters (max spots, min area, threshold)
- Multiple beams tracking with CSV export
- Interactive GUI with zoom, screenshots, and sequence recording
- Exposure and gain control via sliders and keyboard input

## Prerequisites

- Python 3.10 or newer (recommended: 3.12)
- Camera driver/SDK for your hardware (see below)

## Camera Compatibility

This software works with Allied Vision, Dahua, and ADF cameras. Make sure you have the official drivers and SDK installed for your specific camera.

For Allied Vision cameras, download and install the VimbaX SDK from the [Allied Vision website](https://www.alliedvision.com/en/products/software/vimba-x-sdk/). The `vmbpy` Python module is included with the SDK and will be installed automatically by `run.bat`.

Please refer to the individual camera manufacturer's instructions for driver and SDK installation.

## Quick Start

The easiest way to run the application is with the included launcher:

```
run.bat
```

This will create a virtual environment, install all dependencies (including `vmbpy` from the VimbaX SDK if installed), and start the application. On subsequent runs it skips the setup.

## Manual Installation

1. Clone the repository:

    ```
    git clone https://github.com/2DEG/LaserCameraViewer
    cd LaserCameraViewer
    ```

2. Create a virtual environment and install dependencies:

    ```
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. Install VmbPy from VimbaX SDK (Allied Vision cameras only):

    ```
    pip install "C:\Program Files\Allied Vision\Vimba X\api\python\vmbpy-1.2.0-py3-none-win_amd64.whl"
    ```

4. Run the application:

    ```
    python main.py
    ```

## Logs

Application logs are written to the `logs/` directory. Each session creates a new log file named by date and time.
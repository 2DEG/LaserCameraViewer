# Beam Alignment System

Beam Alignment System is an open-source Python application for real-time video processing. This system can detect ellipses in video frames, which is useful for various types of analysis. 

## Features

- Real-time video processing
- Ellipse (laser beam) detection in video frames
- Multiple beams tracking 
- Interactive GUI

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You have installed the required Python version: `3.8`.
- You have installed the required packages: `OpenCV`, `wxPython`, `numpy`, `PIL`, and others as per the `requirements.txt` file.

## Camera Compatibility

This software is designed to work out-of-the-box with Dahua and Allied Vision cameras. Before running the software, make sure you have the official drivers and SDK installed for your specific camera and operating system.

For Allied Vision cameras, you can download Vimba X from the official [Allied Vision website](https://www.alliedvision.com/en/products/software/vimba-x-sdk/).

You will also need the `vbmpy` Python module, which is different from the `vimba` module. The `vbmpy` module can be downloaded from the official [Allied Vision GitHub page](https://github.com/alliedvision/VmbPy). 

Please refer to the individual camera manufacturer's instructions for driver and SDK installation.

## Installing Beam Alignment System

To install Beam Alignment System, follow these steps:

1. Clone the repository:

    ```
    git clone https://github.com/2DEG/LaserCameraViewer
    ```

2. Navigate to the project directory:

    ```
    cd LaserCameraViewer
    ```

3. Install the necessary requirements:

    ```
    pip install -r requirements.txt
    ```

## Running Beam Alignment System

    ```
    python main.py
    ```


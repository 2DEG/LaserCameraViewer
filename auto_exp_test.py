import os
import harvesters
print(harvesters.__version__)

import numpy as np
import cv2
from harvesters.core import Harvester
from harvesters.core import PayloadImage
from genicam.gentl import TimeoutException
from genicam.genapi import SingleChunkData
import time

from genicam import gentl

# gentl.DataStream.ds_get_buffer_chunk_data()

# _buffer._get_single_chunk_data_list() returns single chunk data
# single.ChunkID
# single.ChunkOffset
# single.ChunkLength
scd = SingleChunkData


# DSGetBufferInfo()
# BUFFER_INFO_CONTAINS_CHUNKDATA
# PAYLOAD_TYPE_CHUNK_DATA

# ia._update_chunk_data

# configurations
imshowWidth = 1080
fps = 30.0

h = Harvester()
# ATTENTION! Please use the CTI file in the original location!
path = os.path.abspath(r'C:\Users\drak.admin\Desktop\dahua_cam\dahua_camera_gui\CTI\mvGenTLProducer.cti')
#path = os.path.abspath(r'C:\Program Files\Baumer GAPI SDK (64 Bit)\Components\Bin\bgapi2_usb.cti')
print(path)

h.add_cti_file(path)
h.update_device_info_list()
ia = h.create_image_acquirer(0)

ia.keep_latest = True
ia.num_filled_buffers_to_hold = 1

# Set chunk mode active / enable chunk / get exposure time in data packet
# ia.remote_device.node_map.ComponentSelector = 'Range'
# ia.remote_device.node_map.ComponentEnable.value = True

# Activate Chunk Mode
#if ia.remote_device.node_map.ChunkModeActive.
# ia.remote_device.node_map.ChunkModeActive.value = True

# ia.remote_device.node_map.ChunkSelector.value = 'Image'
# ia.remote_device.node_map.ChunkEnable.value = True
# ia.remote_device.node_map.ChunkSelector.value = 'ExposureTime'
# ia.remote_device.node_map.ChunkEnable.value = True
ia.remote_device.node_map.GainAuto.value = 'Continuous'
# ia.remote_device.node_map.ChunkEnable.value = True
# ia.remote_device.node_map.ChunkSelector.value = 'Gain'
# ia.remote_device.node_map.ChunkEnable.value = True

# window
WINDOW_NAME = 'harvesters'
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_GUI_NORMAL)

image = None
ia.remote_device.node_map.ExposureTime.set_value(5000.0)
ia.start_acquisition()

start = time.time()
newExp = ia.remote_device.node_map.ExposureTime.value

setFlag = True

while True:
    try:
        with ia.fetch_buffer() as buffer:

            component = buffer.payload.components[0]
            # Reshape and convert 2-dimensional to 3-dimensional array - Mono Camera!!
            image = cv2.cvtColor(component.data.copy().reshape(component.height, component.width), cv2.COLOR_GRAY2RGB)
            # resize to fit in imshow
            image = cv2.resize(image, (0, 0), fx=imshowWidth/component.width, fy=imshowWidth/component.width)

            exposureTime = ia.remote_device.node_map.ChunkExposureTime.value
            # gain = ia.remote_device.node_map.Gain.value

        if newExp == exposureTime:
            end = time.time()
            newExp = exposureTime + 1000.0
            print(format(end-start, '3.3f') + ' s for exposure Time ' + str(exposureTime) + " / gain: " + str(None))
            ia.remote_device.node_map.ExposureTime.set_value(newExp)
            start = time.time()
        else:
            print("exposure time: " + str(exposureTime))

    except TimeoutException:
        print("Timeout ocurred waiting for image.")
    except ValueError as err:
        print(err)

    # Show the image if possible
    if image is not None:

        # resize window if necessary
        if image.shape[1] is not cv2.getWindowImageRect(WINDOW_NAME)[2] and \
                image.shape[0] is not cv2.getWindowImageRect(WINDOW_NAME)[3]:
            cv2.resizeWindow(WINDOW_NAME, image.shape[1], image.shape[0])

        # show image
        cv2.imshow(
            WINDOW_NAME,
            image,
        )

    # Keyboard handling
    keypress = cv2.waitKey(1)

    if keypress == 27 or cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
        #  # escape key pressed or window has been closed (x button clicked)
        break

cv2.destroyWindow(WINDOW_NAME)
if ia is not None:
    ia.stop_image_acquisition()
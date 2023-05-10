#!/usr/bin/env python
# coding: utf-8
'''
Created on 2017-10-25

@author: 
'''

# from ImageConvert import *
# from MVSDK import *
import time
import datetime
import numpy
import cv2
import gc

import cProfile

g_cameraStatusUserInfo = b"statusInfo"


def deviceLinkNotify(connectArg, linkInfo):
	if ( EVType.offLine == connectArg.contents.m_event ):
		print("camera has off line, userInfo [%s]" %(c_char_p(linkInfo).value))
	elif ( EVType.onLine == connectArg.contents.m_event ):
		print("camera has on line, userInfo [%s]" %(c_char_p(linkInfo).value))
	

# connectCallBackFuncEx = connectCallBackEx(deviceLinkNotify)


def subscribeCameraStatus(camera):

	eventSubscribe = pointer(GENICAM_EventSubscribe())
	eventSubscribeInfo = GENICAM_EventSubscribeInfo()
	eventSubscribeInfo.pCamera = pointer(camera)
	nRet = GENICAM_createEventSubscribe(byref(eventSubscribeInfo), byref(eventSubscribe))
	if ( nRet != 0):
		print("create eventSubscribe fail!")
		return -1
	
	nRet = eventSubscribe.contents.subscribeConnectArgsEx(eventSubscribe, connectCallBackFuncEx, g_cameraStatusUserInfo)
	if ( nRet != 0 ):
		print("subscribeConnectArgsEx fail!")

		eventSubscribe.contents.release(eventSubscribe)
		return -1  
	

	eventSubscribe.contents.release(eventSubscribe) 
	return 0


def unsubscribeCameraStatus(camera):
  
	eventSubscribe = pointer(GENICAM_EventSubscribe())
	eventSubscribeInfo = GENICAM_EventSubscribeInfo()
	eventSubscribeInfo.pCamera = pointer(camera)
	nRet = GENICAM_createEventSubscribe(byref(eventSubscribeInfo), byref(eventSubscribe))
	if ( nRet != 0):
		print("create eventSubscribe fail!")
		return -1
		
	nRet = eventSubscribe.contents.unsubscribeConnectArgsEx(eventSubscribe, connectCallBackFuncEx, g_cameraStatusUserInfo)
	if ( nRet != 0 ):
		print("unsubscribeConnectArgsEx fail!")
	   
		eventSubscribe.contents.release(eventSubscribe)
		return -1
	
	eventSubscribe.contents.release(eventSubscribe)
	return 0   
   

def openCamera(camera):

	nRet = camera.connect(camera, c_int(GENICAM_ECameraAccessPermission.accessPermissionControl))
	if ( nRet != 0 ):
		print("camera connect fail!")
		return -1
	else:
		print("camera connect success.")
  
	nRet = subscribeCameraStatus(camera)
	if ( nRet != 0 ):
		print("subscribeCameraStatus fail!")
		return -1

	return 0

def closeCamera(camera):

	nRet = unsubscribeCameraStatus(camera)
	if ( nRet != 0 ):
		print("unsubscribeCameraStatus fail!")
		return -1
  
	nRet = camera.disConnect(byref(camera))
	if ( nRet != 0 ):
		print("disConnect camera fail!")
		return -1
	
	return 0    

def setExposureTime(camera, dVal):

	exposureTimeNode = pointer(GENICAM_DoubleNode())
	exposureTimeNodeInfo = GENICAM_DoubleNodeInfo() 
	exposureTimeNodeInfo.pCamera = pointer(camera)
	exposureTimeNodeInfo.attrName = b"ExposureTime"
	nRet = GENICAM_createDoubleNode(byref(exposureTimeNodeInfo), byref(exposureTimeNode))
	if ( nRet != 0 ):
		print("create ExposureTime Node fail!")
		return -1
	  
	nRet = exposureTimeNode.contents.setValue(exposureTimeNode, c_double(dVal))  
	if ( nRet != 0 ):
		print("set ExposureTime value [%f]us fail!"  % (dVal))
		exposureTimeNode.contents.release(exposureTimeNode)
		return -1
	else:
		print("set ExposureTime value [%f]us success." % (dVal))
			
	exposureTimeNode.contents.release(exposureTimeNode)    
	return 0

def getExposureTime(camera):
	# 通用属性设置:设置曝光 --根据属性类型，直接构造属性节点。如曝光是 double类型，构造doubleNode节点
	exposureTimeNode = pointer(GENICAM_DoubleNode())
	exposureTimeNodeInfo = GENICAM_DoubleNodeInfo() 
	exposureTimeNodeInfo.pCamera = pointer(camera)
	exposureTimeNodeInfo.attrName = b"ExposureTime"
	nRet = GENICAM_createDoubleNode(byref(exposureTimeNodeInfo), byref(exposureTimeNode))
	if ( nRet != 0 ):
		print("create ExposureTime Node fail!")
		return -1
	  
	# 设置曝光时间
	exp_time = pointer(c_double())
	nRet = exposureTimeNode.contents.getValue(exposureTimeNode, exp_time)
	# print(gain.contents)
	# gain = int.from_bytes(gain, "big")
	exp_time = exp_time.contents.value
	
	print(nRet)
	if ( nRet != 0 ):
		print("get ExposureTime value {:.1f} us fail!".format(exp_time))
		# 释放相关资源
		exposureTimeNode.contents.release(exposureTimeNode)
		return -1
	else:
		print("get ExposureTime value {:.1f} us success.".format(exp_time))
			
	# 释放节点资源     
	exposureTimeNode.contents.release(exposureTimeNode)    
	return exp_time

def setGain(camera, dVal):
	gainNode = pointer(GENICAM_DoubleNode())
	gainNodeInfo = GENICAM_DoubleNodeInfo() 
	gainNodeInfo.pCamera = pointer(camera)
	gainNodeInfo.attrName = b"GainRaw"
	nRet = GENICAM_createDoubleNode(byref(gainNodeInfo), byref(gainNode))
	if ( nRet != 0 ):
		print("create GainRaw Node fail!")
		return -1
	  
	nRet = gainNode.contents.setValue(gainNode, c_double(dVal))  
	if ( nRet != 0 ):
		print("set GainRaw value [%f]us fail!"  % (dVal))
		gainNode.contents.release(gainNode)
		return -1
	else:
		print("set GainRaw value [%f]us success." % (dVal))
			
	gainNode.contents.release(gainNode)    
	return 0

def getGain(camera):
	gainNode = pointer(GENICAM_DoubleNode())
	gainNodeInfo = GENICAM_DoubleNodeInfo() 
	gainNodeInfo.pCamera = pointer(camera)
	gainNodeInfo.attrName = b"GainRaw"
	nRet = GENICAM_createDoubleNode(byref(gainNodeInfo), byref(gainNode))
	if ( nRet != 0 ):
		print("create GainRaw Node fail!")
		return -1
	  
	# 设置曝光时间
	gain = pointer(c_double())
	nRet = gainNode.contents.getValue(gainNode, gain)
	# print(gain.contents)
	# gain = int.from_bytes(gain, "big")
	gain = gain.contents.value
	
	print(nRet)
	if ( nRet != 0 ):
		print("get GainRaw value {:.1f} us fail!".format(gain))
		# 释放相关资源
		gainNode.contents.release(gainNode)
		return -1
	else:
		print("get GainRaw value {:.1f} us success.".format(gain))
			
	# 释放节点资源     
	gainNode.contents.release(gainNode)    
	return gain
	
def enumCameras():

	system = pointer(GENICAM_System())
	nRet = GENICAM_getSystemInstance(byref(system))
	if ( nRet != 0 ):
		print("getSystemInstance fail!")
		return None, None

	cameraList = pointer(GENICAM_Camera()) 
	cameraCnt = c_uint()
	nRet = system.contents.discovery(system, byref(cameraList), byref(cameraCnt), c_int(GENICAM_EProtocolType.typeAll));
	if ( nRet != 0 ):
		print("discovery fail!")
		return None, None
	elif cameraCnt.value < 1:
		print("discovery no camera!")
		return None, None
	else:
		print("cameraCnt: " + str(cameraCnt.value))
		return cameraCnt.value, cameraList
 

def setROI(camera, OffsetX, OffsetY, nWidth, nHeight):
	widthMaxNode = pointer(GENICAM_IntNode())
	widthMaxNodeInfo = GENICAM_IntNodeInfo() 
	widthMaxNodeInfo.pCamera = pointer(camera)
	widthMaxNodeInfo.attrName = b"WidthMax"
	nRet = GENICAM_createIntNode(byref(widthMaxNodeInfo), byref(widthMaxNode))
	if ( nRet != 0 ):
		print("create WidthMax Node fail!")
		return -1
	
	oriWidth = c_longlong()
	nRet = widthMaxNode.contents.getValue(widthMaxNode, byref(oriWidth))
	if ( nRet != 0 ):
		print("widthMaxNode getValue fail!")
		widthMaxNode.contents.release(widthMaxNode)
		return -1  
	
	widthMaxNode.contents.release(widthMaxNode)
	
	heightMaxNode = pointer(GENICAM_IntNode())
	heightMaxNodeInfo = GENICAM_IntNodeInfo() 
	heightMaxNodeInfo.pCamera = pointer(camera)
	heightMaxNodeInfo.attrName = b"HeightMax"
	nRet = GENICAM_createIntNode(byref(heightMaxNodeInfo), byref(heightMaxNode))
	if ( nRet != 0 ):
		print("create HeightMax Node fail!")
		return -1
	
	oriHeight = c_longlong()
	nRet = heightMaxNode.contents.getValue(heightMaxNode, byref(oriHeight))
	if ( nRet != 0 ):
		print("heightMaxNode getValue fail!")
		heightMaxNode.contents.release(heightMaxNode)
		return -1

	heightMaxNode.contents.release(heightMaxNode)
		
	if ( ( oriWidth.value < (OffsetX + nWidth)) or ( oriHeight.value < (OffsetY + nHeight)) ):
		print("please check input param!")
		return -1
	
	widthNode = pointer(GENICAM_IntNode())
	widthNodeInfo = GENICAM_IntNodeInfo() 
	widthNodeInfo.pCamera = pointer(camera)
	widthNodeInfo.attrName = b"Width"
	nRet = GENICAM_createIntNode(byref(widthNodeInfo), byref(widthNode))
	if ( nRet != 0 ):
		print("create Width Node fail!") 
		return -1
	
	nRet = widthNode.contents.setValue(widthNode, c_longlong(nWidth))
	if ( nRet != 0 ):
		print("widthNode setValue [%d] fail!" % (nWidth))
		widthNode.contents.release(widthNode)
		return -1  
	

	widthNode.contents.release(widthNode)
	
	heightNode = pointer(GENICAM_IntNode())
	heightNodeInfo = GENICAM_IntNodeInfo() 
	heightNodeInfo.pCamera = pointer(camera)
	heightNodeInfo.attrName = b"Height"
	nRet = GENICAM_createIntNode(byref(heightNodeInfo), byref(heightNode))
	if ( nRet != 0 ):
		print("create Height Node fail!")
		return -1
	
	nRet = heightNode.contents.setValue(heightNode, c_longlong(nHeight))
	if ( nRet != 0 ):
		print("heightNode setValue [%d] fail!" % (nHeight))
		heightNode.contents.release(heightNode)
		return -1    
	
	heightNode.contents.release(heightNode)    
	
	OffsetXNode = pointer(GENICAM_IntNode())
	OffsetXNodeInfo = GENICAM_IntNodeInfo() 
	OffsetXNodeInfo.pCamera = pointer(camera)
	OffsetXNodeInfo.attrName = b"OffsetX"
	nRet = GENICAM_createIntNode(byref(OffsetXNodeInfo), byref(OffsetXNode))
	if ( nRet != 0 ):
		print("create OffsetX Node fail!")
		return -1
	
	nRet = OffsetXNode.contents.setValue(OffsetXNode, c_longlong(OffsetX))
	if ( nRet != 0 ):
		print("OffsetX setValue [%d] fail!" % (OffsetX))
		OffsetXNode.contents.release(OffsetXNode)
		return -1    
	
	OffsetXNode.contents.release(OffsetXNode)  
	
	OffsetYNode = pointer(GENICAM_IntNode())
	OffsetYNodeInfo = GENICAM_IntNodeInfo() 
	OffsetYNodeInfo.pCamera = pointer(camera)
	OffsetYNodeInfo.attrName = b"OffsetY"
	nRet = GENICAM_createIntNode(byref(OffsetYNodeInfo), byref(OffsetYNode))
	if ( nRet != 0 ):
		print("create OffsetY Node fail!")
		return -1
	
	nRet = OffsetYNode.contents.setValue(OffsetYNode, c_longlong(OffsetY))
	if ( nRet != 0 ):
		print("OffsetY setValue [%d] fail!" % (OffsetY))
		OffsetYNode.contents.release(OffsetYNode)
		return -1    
	
	OffsetYNode.contents.release(OffsetYNode)   
	return 0

def connect_camera(camera):
	nRet = openCamera(camera)
	if ( nRet != 0 ):
		print("openCamera fail.")
		return -1

def create_stream_source(camera):
	#ToDo: Check if camera is open
	streamSourceInfo = GENICAM_StreamSourceInfo()
	streamSourceInfo.channelId = 0
	streamSourceInfo.pCamera = pointer(camera)

	streamSource = pointer(GENICAM_StreamSource())
	nRet = GENICAM_createStreamSource(pointer(streamSourceInfo), byref(streamSource))
	if ( nRet != 0 ):
		print("create StreamSource fail!")
		return -1
	
	return streamSource

def start_grabbing(stream_source):
	# Start grabbing
	nRet = stream_source.contents.startGrabbing(stream_source, c_ulonglong(0), \
											   c_int(GENICAM_EGrabStrategy.grabStrartegySequential))
	if( nRet != 0):
		print("startGrabbing fail!")
		stream_source.contents.release(stream_source)   
		return -1	

def stop_grabbing(stream_source):
	nRet = stream_source.contents.stopGrabbing(stream_source)
	if ( nRet != 0 ):
		print("stopGrabbing fail!")
		stream_source.contents.release(stream_source)  
		return -1

def close_stream_source(stream_source, camera):
	nRet = closeCamera(camera)
	if ( nRet != 0 ):
		print("closeCamera fail")
		stream_source.contents.release(stream_source)   
		return -1
	 
	stream_source.contents.release(stream_source)  


def get_frame(stream_source):
	frame = pointer(GENICAM_Frame())
	nRet = stream_source.contents.getFrame(stream_source, byref(frame), c_uint(1000))
	if ( nRet != 0 ):
		print("getFrame fail! Timeout:[1000]ms")
		# 释放相关资源
		stream_source.contents.release(stream_source)   
		return -1 
	# else:
		# print("getFrame success BlockId = [" + str(frame.contents.getBlockId(frame)) + "], get frame time: " + str(datetime.datetime.now()))
	  
	nRet = frame.contents.valid(frame)
	if ( nRet != 0 ):
		print("frame is invalid!")
		# 释放驱动图像缓存资源
		frame.contents.release(frame)
		# 释放相关资源
		stream_source.contents.release(stream_source)
		return -1 
	# 给转码所需的参数赋值
	imageParams = IMGCNV_SOpenParam()
	imageParams.dataSize    = frame.contents.getImageSize(frame)
	imageParams.height      = frame.contents.getImageHeight(frame)
	imageParams.width       = frame.contents.getImageWidth(frame)
	imageParams.paddingX    = frame.contents.getImagePaddingX(frame)
	imageParams.paddingY    = frame.contents.getImagePaddingY(frame)
	imageParams.pixelForamt = frame.contents.getImagePixelFormat(frame)

	# print("Size: {}x{}".format(imageParams.width, imageParams.height))
	# 将裸数据图像拷出
	imageBuff = frame.contents.getImage(frame)
	userBuff = c_buffer(b'\0', imageParams.dataSize)
	memmove(userBuff, c_char_p(imageBuff), imageParams.dataSize)
	# 释放驱动图像缓存
	frame.contents.release(frame)
	# 如果图像格式是 Mono8 直接使用
	if imageParams.pixelForamt == EPixelType.gvspPixelMono8:
		grayByteArray = bytearray(userBuff)
		cvImage = numpy.array(grayByteArray).reshape(imageParams.height, imageParams.width)
	else:
		# 转码 => BGR24
		rgbSize = c_int()
		rgbBuff = c_buffer(b'\0', imageParams.height * imageParams.width * 3)
		nRet = IMGCNV_ConvertToBGR24(cast(userBuff, c_void_p), \
									 byref(imageParams), \
									 cast(rgbBuff, c_void_p), \
									 byref(rgbSize))

		colorByteArray = bytearray(rgbBuff)
		cvImage = numpy.array(colorByteArray).reshape(imageParams.height, imageParams.width, 3)
		# image = cv2.cvtColor(cvImage, cv2.COLOR_RGB2GRAY)
		# cvImage = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB) # Kek
		# cProfile.run('detect_circles(cvImage)')
		# print("cvImage Max: ",cvImage.max())
		# print(cvImage[2])
		# max_intensity = cvImage.max()
		# return detect_ellipses(cvImage)
		return cvImage

# def detect_circles(img):
# 	# img = cv2.imread('eyes.jpg', cv2.IMREAD_COLOR)
  
# 	# Convert to grayscale.
# 	gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
# 	img = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
	
# 	# Blur using 3 * 3 kernel.
# 	# gray_blurred = cv2.blur(gray, (3, 3))
	
# 	# Apply Hough transform on the blurred image.
# 	detected_circles = cv2.HoughCircles(gray, 
# 					   cv2.HOUGH_GRADIENT, 1, 500, param1 = 60,
# 				   param2 = 30, minRadius = 10, maxRadius = 1000)
	
# 	# Draw circles that are detected.
# 	if detected_circles is not None:
	
# 		# Convert the circle parameters a, b and r to integers.
# 		detected_circles = numpy.uint16(numpy.around(detected_circles))
	
# 		for pt in detected_circles[0, :]:
# 			a, b, r = pt[0], pt[1], pt[2]
	
# 			# Draw the circumference of the circle.
# 			cv2.circle(img, (a, b), r, (0, 255, 0), 2)
	
# 			# Draw a small circle (of radius 1) to show the center.
# 			cv2.circle(img, (a, b), 1, (0, 0, 255), 3)

# 	return img

# def detect_ellipses(img):

# 	# Load picture, convert to grayscale and detect edges
# 	# image_rgb = data.coffee()[0:220, 160:420]
# 	# image_gray = color.rgb2gray(image_rgb)
# 	gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
# 	# (_, gray, _) = cv2.split(img)
# 	# r_b = numpy.zeros(gray.shape, numpy.uint8)
# 	# new_y = new_y.astype(np.uint8)
# 	# print(r_b.shape)
# 	# print(gray.shape)
# 	# img = cv2.merge((r_b, gray, r_b))
# 	img = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
# 	# edges = canny(gray, sigma=2.0, low_threshold=0.55, high_threshold=0.8)

# 	thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)[1]
	
# 	# Dilate with elliptical shaped kernel
# 	kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
# 	dilate = cv2.dilate(thresh, kernel, iterations=2)
	
# 	# Find contours, filter using contour threshold area, draw ellipse
# 	cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# 	# print(cnts)
# 	cnts = cnts[0] if len(cnts) == 2 else cnts[1]
	
# 	for c in cnts:
# 		area = cv2.contourArea(c)
# 		# print("Hi!")
# 		if area > 50:
# 			ellipse = cv2.fitEllipse(c)
# 			# print(ellipse)
# 			# (xc, yc), (ax, by, e = cv2.fitEllipse(c)
# 			# print(ellipse[0])
# 			a, b = ellipse[0]
# 			a = int(a)
# 			b = int(b)
# 			# c = numpy.zeros(gray.shape)
# 			# c[a-100:a+100, b-100:b+100] = gray[a-100:a+100, b-100:b+100]
# 			# print("Argmax: ", numpy.where(c == c.max()), c.shape)
# 			# print("A, B: ", a, b)
# 			delta = 100
# 			# print(a, b)
# 			# cv2.ellipse(img, (xc, yc), (ax, by), e, (0,255,0), 2)
# 			cv2.line(img, (a-delta, b), (a+delta, b), (255, 0, 0), 2)
# 			cv2.line(img, (a, b-delta), (a, b+delta), (255, 0, 0), 2)
# 			# cv2.circle(img, (int(a), int(b)), 1, (0, 0, 255), 3)
# 			cv2.ellipse(img, ellipse, (0,255,0), 2)
			
	
# 	return img

def demo():    
	cameraCnt, cameraList = enumCameras()
	if cameraCnt is None:
		return -1
	
	for index in range(0, cameraCnt):
		camera = cameraList[index]
		print("\nCamera Id = " + str(index))
		print("Key           = " + str(camera.getKey(camera)))
		print("vendor name   = " + str(camera.getVendorName(camera)))
		print("Model  name   = " + str(camera.getModelName(camera)))
		print("Serial number = " + str(camera.getSerialNumber(camera)))
		
	camera = cameraList[0]

	# nRet = openCamera(camera)
	# if ( nRet != 0 ):
	# 	print("openCamera fail.")
	# 	return -1
	connect_camera(camera)
		
	# streamSourceInfo = GENICAM_StreamSourceInfo()
	# streamSourceInfo.channelId = 0
	# streamSourceInfo.pCamera = pointer(camera)
	  
	# streamSource = pointer(GENICAM_StreamSource())
	# nRet = GENICAM_createStreamSource(pointer(streamSourceInfo), byref(streamSource))
	# if ( nRet != 0 ):
	# 	print("create StreamSource fail!")
	# 	return -1
	stream_source = create_stream_source(camera)
	
	# # 通用属性设置:设置触发模式为off --根据属性类型，直接构造属性节点。如触发模式是 enumNode，构造enumNode节点
	# # 自由拉流：TriggerMode 需为 off
	# trigModeEnumNode = pointer(GENICAM_EnumNode())
	# trigModeEnumNodeInfo = GENICAM_EnumNodeInfo() 
	# trigModeEnumNodeInfo.pCamera = pointer(camera)
	# trigModeEnumNodeInfo.attrName = b"TriggerMode"
	# nRet = GENICAM_createEnumNode(byref(trigModeEnumNodeInfo), byref(trigModeEnumNode))
	# if ( nRet != 0 ):
	#     print("create TriggerMode Node fail!")
	#     # 释放相关资源
	#     streamSource.contents.release(streamSource) 
	#     return -1
	
	# nRet = trigModeEnumNode.contents.setValueBySymbol(trigModeEnumNode, b"Off")
	# if ( nRet != 0 ):
	#     print("set TriggerMode value [Off] fail!")
	#     # 释放相关资源
	#     trigModeEnumNode.contents.release(trigModeEnumNode)
	#     streamSource.contents.release(streamSource) 
	#     return -1
	  
	# # 需要释放Node资源    
	# trigModeEnumNode.contents.release(trigModeEnumNode) 

	# 开始拉流
	# nRet = streamSource.contents.startGrabbing(streamSource, c_ulonglong(0), \
	# 										   c_int(GENICAM_EGrabStrategy.grabStrartegySequential))
	# if( nRet != 0):
	# 	print("startGrabbing fail!")
	# 	# 释放相关资源
	# 	streamSource.contents.release(streamSource)   
	# 	return -1
	start_grabbing(stream_source)

	isGrab = True

	while isGrab :
		cvImage = get_frame(stream_source)
	# 	# 主动取图
	# 	frame = pointer(GENICAM_Frame())
	# 	nRet = streamSource.contents.getFrame(streamSource, byref(frame), c_uint(1000))
	# 	if ( nRet != 0 ):
	# 		print("getFrame fail! Timeout:[1000]ms")
	# 		# 释放相关资源
	# 		streamSource.contents.release(streamSource)   
	# 		return -1 
	# 	else:
	# 		print("getFrame success BlockId = [" + str(frame.contents.getBlockId(frame)) + "], get frame time: " + str(datetime.datetime.now()))
		  
	# 	nRet = frame.contents.valid(frame)
	# 	if ( nRet != 0 ):
	# 		print("frame is invalid!")
	# 		# 释放驱动图像缓存资源
	# 		frame.contents.release(frame)
	# 		# 释放相关资源
	# 		streamSource.contents.release(streamSource)
	# 		return -1 

	# 	# 给转码所需的参数赋值
	# 	imageParams = IMGCNV_SOpenParam()
	# 	imageParams.dataSize    = frame.contents.getImageSize(frame)
	# 	imageParams.height      = frame.contents.getImageHeight(frame)
	# 	imageParams.width       = frame.contents.getImageWidth(frame)
	# 	imageParams.paddingX    = frame.contents.getImagePaddingX(frame)
	# 	imageParams.paddingY    = frame.contents.getImagePaddingY(frame)
	# 	imageParams.pixelForamt = frame.contents.getImagePixelFormat(frame)

	# 	# 将裸数据图像拷出
	# 	imageBuff = frame.contents.getImage(frame)
	# 	userBuff = c_buffer(b'\0', imageParams.dataSize)
	# 	memmove(userBuff, c_char_p(imageBuff), imageParams.dataSize)

	# 	# 释放驱动图像缓存
	# 	frame.contents.release(frame)

	# 	# 如果图像格式是 Mono8 直接使用
	# 	if imageParams.pixelForamt == EPixelType.gvspPixelMono8:
	# 		grayByteArray = bytearray(userBuff)
	# 		cvImage = numpy.array(grayByteArray).reshape(imageParams.height, imageParams.width)
	# 	else:
	# 		# 转码 => BGR24
	# 		rgbSize = c_int()
	# 		rgbBuff = c_buffer(b'\0', imageParams.height * imageParams.width * 3)

	# 		nRet = IMGCNV_ConvertToBGR24(cast(userBuff, c_void_p), \
	# 									 byref(imageParams), \
	# 									 cast(rgbBuff, c_void_p), \
	# 									 byref(rgbSize))
	
	# 		colorByteArray = bytearray(rgbBuff)
	# 		cvImage = numpy.array(colorByteArray).reshape(imageParams.height, imageParams.width, 3)
	#    # --- end if ---

		cv2.imshow('myWindow', cvImage)
		gc.collect()

		if (cv2.waitKey(1) >= 0):
			isGrab = False
			break
	# --- end while ---

	cv2.destroyAllWindows()

	# 停止拉流
	# nRet = streamSource.contents.stopGrabbing(streamSource)
	# if ( nRet != 0 ):
	# 	print("stopGrabbing fail!")
	# 	# 释放相关资源
	# 	streamSource.contents.release(streamSource)  
	# 	return -1
	stop_grabbing(stream_source)

	
	# 关闭相机
	# nRet = closeCamera(camera)
	# if ( nRet != 0 ):
	# 	print("closeCamera fail")
	# 	# 释放相关资源
	# 	streamSource.contents.release(streamSource)   
	# 	return -1
	 
	# # 释放相关资源
	# streamSource.contents.release(streamSource)    
	close_stream_source(stream_source, camera)
	
	return 0
	
if __name__=="__main__": 

	nRet = demo()
	if nRet != 0:
		print("Some Error happend")
	print("--------- Demo end ---------")
	# 3s exit
	time.sleep(0.5)

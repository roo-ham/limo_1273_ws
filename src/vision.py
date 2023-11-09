#!/usr/bin/env python
# -*- coding: utf-8 -*-
import rospy
import numpy as np
import cv2
from ar_track_alvar_msgs.msg import AlvarMarkers
from std_msgs.msg import Int8, Int8MultiArray
from rospy.numpy_msg import numpy_msg
from basement import Basement

class VisionImage:
    def __init__(self, base:Basement):
        self.basement = base
        rospy.Subscriber("/hyproject/image_loader/bgr_top",\
            numpy_msg(Int8MultiArray), self.bgr_top_callback)
        rospy.Subscriber("/hyproject/image_loader/bgr_bottom",\
            numpy_msg(Int8MultiArray), self.bgr_bottom_callback)
        print("I'm VisionImage")
    def bgr_top_callback(self, data):
        pass
        #self.basement.bgr_top = np.reshape(list(data.data),\
        #    (128, 256, 3)).astype(np.uint8)
    def bgr_bottom_callback(self, data):
        print(data)
        return
        #self.basement.bgr_bottom = np.reshape(list(data.data),\
        #    (128, 256, 3)).astype(np.uint8)
    def get_yellow(self):
        img = cv2.cvtColor(self.basement.bgr_bottom, cv2.COLOR_BGR2HSV)
        under_yellow = img[:, :, 0] < 15
        over_yellow = img[:, :, 0] > 35
        img[:, :, 0] = np.where(under_yellow, 0, img[:, :, 0])
        img[:, :, 1] = np.where(under_yellow, 50, 255)
        img[:, :, 2] = np.where(under_yellow, 50, 255)
        img[:, :, 0] = np.where(over_yellow, 128, img[:, :, 0])
        img[:, :, 2] = np.where(over_yellow, 50, 255)
        img = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
        cv2.namedWindow("hyproject", cv2.WINDOW_NORMAL)
        cv2.imshow("hyproject", img)
        cv2.waitKey(1)
        return ~(under_yellow & over_yellow)

class VisionMarker:
    def __init__(self, base:Basement):
        self.basement = base
        rospy.Subscriber("/ar_pose_marker", AlvarMarkers, self.callback)
        print("I'm VisionMarker")
    def callback(self, data):
        pass
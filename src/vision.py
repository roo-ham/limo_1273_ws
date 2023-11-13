#!/usr/bin/env python
# -*- coding: utf-8 -*-
import rospy
import numpy as np
import cv2
from basement import Basement
from submodule import Submodule
from sensor_msgs.msg import CompressedImage
from ar_track_alvar_msgs.msg import AlvarMarkers
from cv_bridge import CvBridge

class VisionImage(Submodule):
    def __init__(self, base:Basement):
        super().__init__(base, "VisionImage")
        self.sub_image_raw = rospy.Subscriber("/camera/rgb/image_raw/compressed", CompressedImage, self.callback)
    def get_yellow(self):
        under_yellow = self.basement.img_h < 13
        over_yellow = self.basement.img_h > 37
        return ~(under_yellow | over_yellow)
    def get_white(self):
        over_sat = self.basement.img_s < 64
        over_bri = self.basement.img_v > 150
        return (over_sat & over_bri)
    def get_black(self):
        over_sat = self.basement.img_s < 128
        over_bri = self.basement.img_v < 150
        return (over_sat & over_bri)
    def update(self):
        super().update()

        yellow = self.get_yellow()
        black = self.get_black()
        white = self.get_white()

        yellow = self.get_yellow_border(white, black, yellow)
        identity_size = np.sum(yellow)
        self.basement.global_tan = self.get_global_tangent(identity_size, yellow)
        self.basement.local_tan, self.basement.local_tan_sqaured = self.get_local_tangent(identity_size, yellow)
        
        self.display(white, black, yellow)

    def get_global_tangent(self, identity_size, yellow:np.ndarray) -> float:
        if identity_size <= 0:
            return 0.0
        x_set = yellow * np.arange(-128, 128)
        y_set = ((yellow.T) * np.arange(128-self.basement.bottom_height, 128)).T
        x_set, y_set = np.where(y_set != 0, x_set, 0), np.where(y_set != 0, y_set, 1)
        return np.arctan(np.sum(x_set/y_set) / identity_size)

    def get_local_tangent(self, identity_size, yellow:np.ndarray) -> tuple:
        if identity_size <= 0:
            return 0.0, 0.0
        l_tan = 0.0
        l_tan_squared = 0.0
        for x, y in np.array(np.where(yellow)).T:
            if y == 128 : continue
            base = yellow[-4+x:5+x, -4+y:5+y]
            mask = np.ones_like(base, bool)
            x_set = (mask & base) * np.arange(-4, 5)
            y_set = ((mask & base.T) * np.arange(-4, 5)).T
            x_set, y_set = np.where(y_set != 0, x_set, 0), np.where(y_set != 0, y_set, 1)
            identity_size_local = np.sum(base)
            arctan0 = np.arctan(np.sum(x_set/y_set) / identity_size_local)
            l_tan += arctan0 / identity_size
            l_tan_squared += arctan0**2 / identity_size
        return l_tan, l_tan_squared

    def get_yellow_border(self, white, black, yellow):
        b_height = self.basement.bottom_height
        bw = black | white
        bw[:, 0:254] &= bw[:, 2:256]
        yellow = yellow & ~bw
        y2 = np.zeros((b_height,256), bool)
        y2[0:b_height, 0:255] |= yellow[0:b_height, 0:255] ^ yellow[0:b_height, 1:256]
        y2[0:b_height-1, 0:256] |= yellow[0:b_height-1, 0:256] ^ yellow[1:b_height, 0:256]
        y2[:, 0:8] = False
        y2[:, 248:256] = False
        y2[0:8, :] = False
        y2[b_height-8:b_height, :] = False
        return y2

    def display(self, white, black, yellow):
        img = np.zeros_like(self.basement.get_bgr_bottom())

        img[:, :, 0] = np.where(white, 255, img[:, :, 0])
        img[:, :, 1] = np.where(white, 255, img[:, :, 1])
        img[:, :, 2] = np.where(white, 0, img[:, :, 2])

        img[:, :, 0] = np.where(black, 255, img[:, :, 0])
        img[:, :, 1] = np.where(black, 0, img[:, :, 1])
        img[:, :, 2] = np.where(black, 0, img[:, :, 2])

        img[:, :, 0] = np.where(yellow, 0, img[:, :, 0])
        img[:, :, 1] = np.where(yellow, 255, img[:, :, 1])
        img[:, :, 2] = np.where(yellow, 255, img[:, :, 2])

        cv2.namedWindow("hyproject", cv2.WINDOW_GUI_EXPANDED)
        cv2.imshow("hyproject", img)
        cv2.waitKey(1)
    def callback(self, data):
        super().callback(data)
        bridge = CvBridge()
        origin = bridge.compressed_imgmsg_to_cv2(data, "bgr8")
        origin = cv2.resize(origin, (256, 256))
        self.basement.set_bgr(origin, origin[256-self.basement.bottom_height:256, :, :])

class VisionMarker(Submodule):
    def __init__(self, base:Basement):
        super().__init__(base, "VisionMarker")
        self.sub_marker = rospy.Subscriber("/ar_pose_marker", AlvarMarkers, self.callback)
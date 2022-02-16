#
# from PySide6 import QtWidgets, QtCore
#
# from PySide6.QtCore import *

import os
from datetime import datetime
from PySide2 import QtWidgets, QtCore, QtGui
import pandas as pd
from PySide2.QtCore import *

from skimage import io

import cv2
import numpy as np
import time
from pycromanager import Bridge
from matplotlib import pyplot as plt
import csv
import math

# 该类是作为程序后端负责打开并且处理图像的线程
class ImageProcessingThread(QObject):
    # 处理完毕图像数据信号
    show_img_signal = QtCore.Signal(QtGui.QPixmap)
    # 线程接收参数信号
    start_image_signal = QtCore.Signal()
    update_time = QtCore.Signal(float)
    update_save = QtCore.Signal(int)

    def __init__(self):
        super(ImageProcessingThread, self).__init__()
        self.is_paused = False
        self.is_killed = False

        self.track = False
        self.record = False



        self.low = 2
        self.high = 0

        self.flip = False
        self.angle = 2

        self.start_time = time.time()
        # For 30 min
        self.tracking_time = 5

        self.mode = 1

        # for mode1
        self.tracking_frequency = 2

        # for mode2
        self.x_bias = 100

        self.pixel_size = 1.1


        self.right = True

        self.c_x = 834
        self.c_y = 600

        self.points = []
        self.images = []

        self.cwd = os.getcwd()
        self.date = datetime.today().strftime('%Y-%m-%d')
        self.save_path = self.cwd + '/' + self.date
        self.save_path.replace('\\', '/')

        self.show_image_fre = 10
        # self.core, self.stage = self.get_core()
        self.core = ''
        self.stage = ''
        self.bridge = Bridge()

    def get_core(self):
        # get object representing micro-manager core
        core = self.bridge.get_core()

        #### Calling core functions ###
        exposure = core.get_exposure()

        #### Setting and getting properties ####
        # Here we set a property of the core itself, but same code works for device properties
        auto_shutter = core.get_property('Core', 'AutoShutter')
        core.set_property('Core', 'AutoShutter', 0)
        stage = core.get_xy_stage_position()
        return core, stage

    def loop(self):
        i = 0
        j = 0
        while True:
            while self.is_paused:
                time.sleep(0.1)

            if self.is_killed:
                break

            image = self.snap_image()

            if self.track:
                max_point = self.find_max_point(image)
                stage_position = self.core.get_xy_stage_position()
                stage_x = stage_position.get_x()
                stage_y = stage_position.get_y()

                if self.mode == 1:
                    i, point = self.mode1(image,max_point, stage_x, stage_y, self.c_x, self.c_y, i, self.tracking_frequency)
                else:
                    point = self.mode2(image,max_point, stage_x, stage_y, self.c_x, self.c_y, self.x_bias)

                if self.record:
                    self.points.append(point)
                    self.images.append(image)
                    self.update_time.emit(time.time() - self.start_time)
                    if time.time() - self.start_time > self.tracking_time * 60:
                        break

            # if j == self.show_image_fre:
            image_8bit = self.transfer_16bit_to_8bit(image)
            image_b = self.image_bright(image_8bit, self.low, self.high)
            q_image = self.cv_to_qpix(image_b)
            j = 0

            self.show_img_signal.emit(q_image)

            # else:
            #     j += 1

        self.sava_data(self.save_path)

    def sava_data(self, save_path):
        if not os.path.exists(save_path):
            os.mkdir(save_path)
        for i in range(len(self.images)):
            data_name = save_path + '\\' + str(i) + '.tif'
            io.imsave(data_name, self.images[i])
            self.update_save.emit(i)
        head, tail = os.path.split(save_path)
        with open(save_path + '\\' + tail + '.csv', 'w', newline='') as f:
            write = csv.writer(f)
            write.writerows(self.points)

    def mode1(self, image, max_point, stage_x, stage_y, c_x, c_y, i, fre):
        x1 = (c_x - max_point[0]) * self.pixel_size
        y1 = (c_y - max_point[1]) * self.pixel_size
        print(c_x,c_y)
        if self.angle == 2:
            x = stage_x + x1
            y = stage_y + y1
        elif self.angle == 0:
            x = stage_x - x1
            y = stage_y - y1

        if i == fre:

            self.stage = self.core.get_xy_stage_device()
            self.core.set_xy_position(self.stage, x, y)
            i = 0
        else:
            i += 1
        return i, [stage_x, stage_y, max_point[0], max_point[1]]

    def mode2(self, image, max_point, stage_x, stage_y, c_x, c_y, x_bias):
        x1 = (c_x - max_point[0]) * self.pixel_size
        y1 = (c_y - max_point[1]) * self.pixel_size
        print(self.angle)
        if self.angle == 2:
            x = stage_x + x1
            y = stage_y + y1
        elif self.angle == 0:
            x = stage_x - x1
            y = stage_y - y1

        distance = math.dist([max_point[0], max_point[1]], [c_x, c_y])
        if distance > x_bias:
            self.stage = self.core.get_xy_stage_device()
            self.core.set_xy_position(self.stage, x, y)

        return [stage_x, stage_y, max_point[0], max_point[1]]

    def snap_image(self):
        self.core.snap_image()
        tagged_image = self.core.get_tagged_image()
        image = np.reshape(tagged_image.pix,
                           newshape=[tagged_image.tags['Height'], tagged_image.tags['Width']])

        if self.flip:
            image = np.flip(image, 1)

        image = np.rot90(image, self.angle)

        return image

    def find_max_point(self, image):
        shape_x = int(image.shape[1] / 2)
        if not self.right:
            image_slice = image[:,:shape_x]
            index = np.argmax(image_slice)
            r, c = divmod(index, image_slice.shape[1])
            point = (c, r)
        else:
            image_slice = image[: , shape_x:]
            index = np.argmax(image_slice)
            r, c = divmod(index, image_slice.shape[1])
            point = (c + shape_x, r)

        return point

    def transfer_16bit_to_8bit(self, image):
        if image is None:
            return None, None
        min_16bit = np.min(image)
        max_16bit = np.max(image)
        image_8bit = np.array(np.rint(255 * ((image - min_16bit) / (max_16bit - min_16bit))),
                              dtype=np.uint8)

        image_8bit = cv2.resize(image_8bit, dsize=(600, 600), interpolation=cv2.INTER_CUBIC)
        return image_8bit

    def cv_to_qpix(self, img):
        # cv 图片转换成 qpix图片
        qt_img = QtGui.QImage(img.data,  # 数据源
                              img.shape[1],  # 宽度
                              img.shape[0],  # 高度
                              img.shape[1],  # 行字节数
                              QtGui.QImage.Format_Grayscale8)
        return QtGui.QPixmap.fromImage(qt_img)

    def image_bright(self, image, alpha=3, beta=0):
        image_bright = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        return image_bright



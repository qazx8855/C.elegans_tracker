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


# class show_img_signal(QObject):
#     progress = QtCore.Signal(QtGui.QPixmap, dict)
#
# class start_image_process_thread_signal(QObject):
#     progress = QtCore.Signal(dict, int, str, bool)
#
# class Loop_signal (QObject):
#     progress = QtCore.Signal(dict, int, str, bool, int, int)

# 该类是作为程序后端负责打开并且处理图像的线程
class ImageProcessingThread(QObject):
    # 处理完毕图像数据信号
    show_img_signal = QtCore.Signal(QtGui.QPixmap)
    # 线程接收参数信号
    start_image_signal = QtCore.Signal()

    def __init__(self):
        super(ImageProcessingThread, self).__init__()
        self.is_paused = False
        self.is_killed = False

        self.track = False
        self.record = False

        self.points = pd.DataFrame(
            columns=['x', 'y'])
        self.images = []

        self.stage = self.core.get_xy_stage_position()

        self.low = 0
        self.high = 65536

        self.flip = False
        self.angle = 2

        self.start_time = time.time()
        # For 30 min
        self.track_time = 30

        self.mode = 1

        # for mode1
        self.tracking_frequency = 2

        # for mode2
        self.bias_x = 100
        self.bias_y = 100

        self.right = True

        self.c_x = 834
        self.c_y = 600

        self.cwd = os.getcwd()
        date = datetime.today().strftime('%Y-%m-%d')
        self.save_path = self.cwd + '\\' + date

        self.show_image_fre = 10

        with Bridge() as bridge:
            # get object representing micro-manager core
            self.core = bridge.get_core()

            #### Calling core functions ###
            exposure = self.core.get_exposure()

            #### Setting and getting properties ####
            # Here we set a property of the core itself, but same code works for device properties
            auto_shutter = self.core.get_property('Core', 'AutoShutter')
            self.core.set_property('Core', 'AutoShutter', 0)

    def loop(self):
        i = 0
        j = 0
        while 1:
            while self.is_paused:
                time.sleep(0.1)

            if self.is_killed:
                break

            image = self.snap_image()

            if self.track:
                if self.mode == 1:
                    if i < self.tracking_frequency:
                        i, x, y = self.mode1(image, self.c_x, self.c_y, i, self.tracking_frequency)
                elif self.mode == 2:
                    x, y = self.mode2(image, self.c_x, self.c_y, self.x_bias, self.y_bias)

                if time.time() - self.start_time < self.tracking_time * 60:
                    break

                if self.record:
                    self.points = self.points.append(pd.DataFrame({
                        'x': x,
                        'y': y
                    }), ignore_index=True)
                    self.images.append(image)

            if j == self.show_image_fre:
                q_image = self.cv_to_qpix(image)
                j = 0

                self.show_img_signal.emit(q_image)

            else:
                j += 1

        self.sava_data(self.save_path)

    def sava_data(self, data_folder):
        data_name = data_folder + '\\points.csv'
        self.points.to_csv(data_name, sep=',', encoding='utf-8')
        for i in range(len(self.images)):
            data_name = data_folder + '\\' + str(i) + '.tif'
            io.imsave(data_name, self.images[i])

    def mode1(self, image, c_x, c_y, i, fre):
        max_point = self.find_max_point(image)

        stage_x = self.stage.get_x()

        stage_y = self.stage.get_y()

        x1 = (c_x - max_point[0]) * 1.1
        y1 = (c_y - max_point[1]) * 1.1

        if not self.right:
            x = stage_x - x1
            y = stage_y - y1

        else:
            x = stage_x + x1
            y = stage_y + y1

        if i == fre:
            self.core.set_xy_position(self.stage, x, y)
            i = 0
        else:
            i += 1
        return i, x, y

    def mode2(self, image, c_x, c_y, x_bias, y_bias):
        max_point = self.find_max_point(image)

        stage_x = self.stage.get_x()

        stage_y = self.stage.get_y()

        x1 = (c_x - max_point[0]) * 1.1
        y1 = (c_y - max_point[1]) * 1.1

        if not self.right:
            x = stage_x - x1
            y = stage_y - y1

        else:
            x = stage_x + x1
            y = stage_y + y1

        if not max_point[0] - x_bias < max_point[0] < max_point[0] + x_bias \
                and max_point[1] - y_bias < max_point[1] < max_point[1] + y_bias:
            self.core.set_xy_position(self.stage, x, y)
        return x, y

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
        index = np.argmax(image)
        r, c = divmod(index, image.shape[1])
        point = (c, r)
        return point

    def cv_to_qpix(self, img):
        # cv 图片转换成 qpix图片
        qt_img = QtGui.QImage(img.data,  # 数据源
                              img.shape[1],  # 宽度
                              img.shape[0],  # 高度
                              img.shape[1],  # 行字节数
                              QtGui.QImage.Format_Grayscale8)
        return QtGui.QPixmap.fromImage(qt_img)

    def label(self, image, centres, label_radius, bias_row, bias_column):
        for centre in centres:
            label_text = str(centres.index(centre))
            self.draw_rectangle(image, centre[1], centre[0], label_text, label_radius)

            left_row, left_column = self.find_left_centre(centre[1], centre[0], bias_row, bias_column)
            self.draw_rectangle(image, left_column, left_row, label_text, label_radius)
        return image

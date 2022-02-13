import os
import re
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import *
import time
from PySide6.QtGui import *
from PySide6 import QtGui
import sys
from back_end import *
from front_end import *

import pyqtgraph as pg

import numpy as np
import pylab as pl


# ------------------ MainWidget ------------------
class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.start = None
        qfile = QFile('ui.ui')
        qfile.open(QFile.ReadOnly)
        qfile.close()
        # 获取当前程序文件位置
        self.cwd = os.getcwd()
        # 从UI定义中动态创建一个相应的窗口对象
        self.ui = QUiLoader().load(qfile)

        # self.ui = gui.Ui_Form()  # 实例化UI对象
        # self.ui.setupUi(self)  # 初始化

        self.image_name = ''
        self.image_path = ''

        self.image_num = 0
        self.image_8bit = None
        self.image_16bit = None
        self.image_bright = None

        self.stop = False
        self.flip = False

        self.parameter_dict = {
            'alpha': 3, 'beta': 0,
            'peak_circle': 6, 'peak_ratio': 0.4,
            'row_bias': 0, 'column_bias': 0,
            'label_radius': 7,
            'right_black': 0, 'left_black': 0,
            'right_black_bias': 0, 'left_black_bias': 0,
            'right_circle': 5, 'right_ratio': 0.6,
            'left_circle': 5, 'left_ratio': 0.6,
        }

        self.initialization_parameter()

        self.result_dict = {}
        self.results = []

        self.thread = QThread()
        # 实例化线程类
        self.image_process_thread = ImageProcessingThread()
        # moveToThread方法把实例化线程移到Thread管理
        self.image_process_thread.moveToThread(self.thread)
        # 连接槽函数
        self.image_process_thread.start_image_process_thread_signal.connect(self.image_process_thread.image_processing)
        self.image_process_thread.show_img_signal.connect(self.show_image)
        self.image_process_thread.loop_signal.connect(self.image_process_thread.loop)
        # 开启线程,一直挂在后台
        self.thread.start()

        # 部件处理
        self.ui.button_select_file.clicked.connect(self.button_select_file)

        self.ui.button_next.clicked.connect(self.button_next)
        self.ui.button_last.clicked.connect(self.button_last)

        self.ui.button_go.clicked.connect(self.button_go)
        self.ui.button_run.clicked.connect(self.button_run)
        self.ui.button_refresh.clicked.connect(self.button_refresh)

        self.ui.button_pause.clicked.connect(self.button_pause)
        self.ui.button_stop.clicked.connect(self.button_kill)

        self.ui.button_up.clicked.connect(lambda: self.button_refresh(-1, 0))
        self.ui.button_down.clicked.connect(lambda: self.button_refresh(1, 0))
        self.ui.button_left.clicked.connect(lambda: self.button_refresh(0, -1))
        self.ui.button_right.clicked.connect(lambda: self.button_refresh(0, 1))

        self.ui.checkbox_mirror_symmetry.stateChanged.connect(self.checkbox_mirror_symmetry)

        self.ui.text_file_path.setText(self.image_path)

    def button_select_file(self):
        image_path_name, _ = QFileDialog.getOpenFileName(self, 'Select image', '', 'Image files(*.tif)')

        self.image_path, self.image_name = os.path.split(image_path_name)

        self.ui.text_file_path.setText(self.image_path)

        # if self.image_path == '':
        #     self.image_path = QFileDialog.getExistingDirectory(self, 'Select image')
        #     self.ui.text_file_path.setText(self.image_path)
        #     print(self.image_path)
        #     print('\nCancel')

        regex = re.compile(r'\d+')
        if bool(re.search(r'\d', self.image_name)):
            self.image_num = int(max(regex.findall(self.image_name)))
            print(self.image_num)

        self.set_parameter()
        self.image_process_thread.start_image_process_thread_signal.emit(self.parameter_dict,
                                                                         self.image_num, self.image_path, self.flip)

    def button_next(self):
        self.image_num += 1
        self.set_parameter()
        self.image_process_thread.start_image_process_thread_signal.emit(self.parameter_dict,
                                                                         self.image_num, self.image_path, self.flip)

    def button_last(self):
        self.image_num -= 1
        self.set_parameter()
        self.image_process_thread.start_image_process_thread_signal.emit(self.parameter_dict,
                                                                         self.image_num, self.image_path, self.flip)

    def button_kill(self):
        self.image_process_thread.is_killed = True
        time.sleep(0.1)
        self.image_process_thread.is_killed = False

    def button_pause(self):
        if not self.image_process_thread.is_paused:
            self.image_process_thread.is_paused = True
            self.ui.button_pause.setText("Resume")
        else:
            self.image_process_thread.is_paused = False
            self.ui.button_pause.setText("Pause")

        # if self.pause:
        #     self.ui.button_pause.setText('Continue')
        # else:
        #     self.ui.button_pause.setText('Pause')

    def button_go(self):
        self.image_num = int(self.ui.textEdit_num.toPlainText())
        self.set_parameter()
        self.image_process_thread.start_image_process_thread_signal.emit(self.parameter_dict,
                                                                         self.image_num, self.image_path, self.flip)

    def button_run(self):
        start = int(self.ui.textEdit_start.toPlainText())
        end = int(self.ui.textEdit_end.toPlainText())
        self.image_num = start
        self.set_parameter()
        # for i in range(start, end + 1):
        # if self.stop:
        #     break
        self.image_process_thread.loop_signal.emit(self.parameter_dict,
                                                   self.image_num, self.image_path,
                                                   self.flip, start, end)
        self.image_num += 1

    def button_refresh(self, bias_row=0, bias_column=0):
        self.set_parameter()
        self.parameter_dict['row_bias'] += bias_row
        self.parameter_dict['column_bias'] += bias_column
        self.initialization_parameter()
        self.image_process_thread.start_image_process_thread_signal.emit(self.parameter_dict,
                                                                         self.image_num, self.image_path, self.flip)

    def checkbox_mirror_symmetry(self):
        self.flip = not self.flip
        self.set_parameter()
        self.image_process_thread.start_image_process_thread_signal.emit(self.parameter_dict,
                                                                         self.image_num, self.image_path, self.flip)

    def initialization_parameter(self):
        self.ui.textEdit_alpha.setText(str(self.parameter_dict['alpha']))
        self.ui.textEdit_beta.setText(str(self.parameter_dict['beta']))

        self.ui.textEdit_peak_ratio.setText(str(self.parameter_dict['peak_ratio']))
        self.ui.textEdit_peak_circle.setText(str(self.parameter_dict['peak_circle']))

        self.ui.textEdit_right_ratio.setText(str(self.parameter_dict['right_ratio']))
        self.ui.textEdit_right_circle.setText(str(self.parameter_dict['right_circle']))

        self.ui.textEdit_row_bias.setText(str(self.parameter_dict['row_bias']))
        self.ui.textEdit_column_bias.setText(str(self.parameter_dict['column_bias']))

        self.ui.textEdit_left_ratio.setText(str(self.parameter_dict['left_ratio']))
        self.ui.textEdit_left_circle.setText(str(self.parameter_dict['left_circle']))

        self.ui.textEdit_right_black_bias.setText(str(self.parameter_dict['right_black_bias']))
        self.ui.textEdit_left_black_bias.setText(str(self.parameter_dict['left_black_bias']))

    def set_parameter(self):
        self.parameter_dict['alpha'] = float(self.ui.textEdit_alpha.toPlainText())
        self.parameter_dict['beta'] = float(self.ui.textEdit_beta.toPlainText())

        self.parameter_dict['peak_ratio'] = float(self.ui.textEdit_peak_ratio.toPlainText())
        self.parameter_dict['peak_circle'] = int(self.ui.textEdit_peak_circle.toPlainText())

        self.parameter_dict['right_ratio'] = float(self.ui.textEdit_right_ratio.toPlainText())
        self.parameter_dict['right_circle'] = int(self.ui.textEdit_right_circle.toPlainText())

        self.parameter_dict['row_bias'] = int(self.ui.textEdit_row_bias.toPlainText())
        self.parameter_dict['column_bias'] = int(self.ui.textEdit_column_bias.toPlainText())

        self.parameter_dict['left_ratio'] = float(self.ui.textEdit_left_ratio.toPlainText())
        self.parameter_dict['left_circle'] = int(self.ui.textEdit_left_circle.toPlainText())

        self.parameter_dict['right_black_bias'] = int(self.ui.textEdit_right_black_bias.toPlainText())
        self.parameter_dict['left_black_bias'] = int(self.ui.textEdit_left_black_bias.toPlainText())

    def show_image(self, q_pixmap, result_dict):
        self.ui.label_image.setPixmap(q_pixmap)
        self.result_dict = result_dict
        self.set_result()

    def set_result(self):
        # 有用的
        self.initialization_parameter()
        self.ui.textEdit_num.setText(str(self.result_dict['num']))

        self.ui.text_right_coordinate.setText(
            str(self.result_dict['right_row']) + ':' +
            str(self.result_dict['right_column'])
        )
        self.ui.text_right_brightness.setText(str(self.result_dict['right_brightness']))

        self.ui.text_left_coordinate.setText(
            str(self.result_dict['left_row']) + ':' +
            str(self.result_dict['left_column'])
        )
        self.ui.text_left_brightness.setText(str(self.result_dict['left_brightness']))

        self.ui.text_brightness.setText(str(self.result_dict['brightness']))
        self.ui.text_right_black.setText(str(self.result_dict['right_black']))
        self.ui.text_left_black.setText(str(self.result_dict['left_black']))


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = MyWidget()
    # widget.show()
    widget.ui.show()
    sys.exit(app.exec())

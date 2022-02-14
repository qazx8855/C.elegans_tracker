import PySide2
from PySide2.QtWidgets import *
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile


import os
from datetime import datetime
import sys
from back_end import *

import re
import csv

import numpy as np
import random


# ------------------ MainWidget ------------------


class MainWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        designer_file = QFile("track.ui")
        designer_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.ui = loader.load(designer_file, self)
        designer_file.close()

        self.cwd = os.getcwd()
        date = datetime.today().strftime('%Y-%m-%d')
        self.save_path = self.cwd + '\\' + date
        self.ui.text_file_path_2.setText(self.save_path)

        self.thread = QThread()
        # 实例化线程类
        self.i_thread = ImageProcessingThread()
        # moveToThread方法把实例化线程移到Thread管理
        self.i_thread.moveToThread(self.thread)
        # 连接槽函数
        self.i_thread.start_image_process_thread_signal.connect(self.i_thread.loop)
        self.i_thread.show_img_signal.connect(self.show_image)

        # 开启线程,一直挂在后台
        # 开启线程,一直挂在后台
        self.thread.start()

        # 设置默认按钮状态
        self.ui.radioButton_180.setChecked(True)
        self.ui.mode1.setChecked(True)
        self.ui.right.setChecked(True)

        self.ui.buttonGroup.buttonClicked.connect(self.angle_clicked)
        self.ui.buttonGroup_2.buttonClicked.connect(self.mode_clicked)
        self.ui.buttonGroup_3.buttonClicked.connect(self.area_clicked)

        self.ui.checkbox_mirror_symmetry.stateChanged.connect(self.checkbox_mirror_symmetry)

    def checkbox_mirror_symmetry(self):
        self.i_thread.flip = not self.i_thread.flip

        print(self.i_thread.flip)

    def angle_clicked(self):
        button = self.ui.buttonGroup.checkedButton()
        if button.text() == '0':
            self.i_thread.angle = 0

        else:
            self.i_thread.angle = int(int(button.text()) / 90)

        print(self.i_thread.angle)

    def mode_clicked(self):
        button = self.ui.buttonGroup_2.checkedButton()
        if button.text() == 'Mode tracking frequency':
            self.i_thread.mode = 1
        elif button.text() == 'Mode Limit area':
            self.i_thread.mode = 2

        print(self.i_thread.mode)

    def area_clicked(self):
        button = self.ui.buttonGroup_3.checkedButton()
        if button.text() == 'Track right':
            self.i_thread.right = True
        elif button.text() == 'Track left':
            self.i_thread.right = False

        print(self.i_thread.right)

    def button_saving_folder(self):
        self.save_path, _ = QFileDialog.getSaveFileName(self, 'Select save path', self.cwd, 'Image(*.tif)')
        self.ui.text_file_path_2.setText(self.save_path)

    def open(self):
        self.i_thread.is_killed = False
        self.i_thread.track = False
        self.i_thread.record = False
        self.i_thread.start_image_signal.emit()

    def track(self):
        self.i_thread.start_time = time.time()
        self.i_thread.track = True

    def record(self):
        self.i_thread.record = True

    def button_kill(self):
        self.i_thread.is_killed = True

    def button_pause(self):
        if not self.i_thread.is_paused:
            self.i_thread.is_paused = True
            self.ui.button_pause.setText("Resume")
        else:
            self.i_thread.is_paused = False
            self.ui.button_pause.setText("Pause")

    def show_image(self, q_pixmap):
        self.ui.label_image.setPixmap(q_pixmap)

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self,
                                               'Quit',
                                               "Quit?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            os._exit(0)
        else:
            event.ignore()



if __name__ == '__main__':
    dirname = os.path.dirname(PySide2.__file__)
    plugin_path = os.path.join(dirname, 'plugins', 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
    print(plugin_path)
    app = QApplication([])
    window = MainWidget()
    window.show()
    app.exec_()

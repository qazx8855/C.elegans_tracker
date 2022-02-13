# ------------------ PySide2 - Qt Designer - Matplotlib ------------------
from PySide2.QtWidgets import *
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from datetime import datetime
import sys
from back_end import *
import os
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


        self.thread = QThread()
        # 实例化线程类
        self.image_process_thread = ImageProcessingThread()
        # moveToThread方法把实例化线程移到Thread管理
        self.image_process_thread.moveToThread(self.thread)
        # 连接槽函数

        # 开启线程,一直挂在后台
        self.thread.start()




    def button_saving_folder(self):
        self.save_path, _ = QFileDialog.getSaveFileName(self, 'Select save path', self.cwd, 'Image(*.tif)')
        self.ui.text_file_path_2.setText(self.save_path)




if __name__ == '__main__':
    app = QApplication([])
    window = MainWidget()
    window.show()
    app.exec_()

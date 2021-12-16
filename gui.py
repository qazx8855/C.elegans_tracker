# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'demo1mnwJUh.ui'
##
## Created by: Qt User Interface Compiler version 6.2.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QPushButton, QSizePolicy, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1023, 497)
        self.button = QPushButton(Form)
        self.button.setObjectName(u"button")
        self.button.setGeometry(QRect(20, 380, 141, 41))
        self.button_2 = QPushButton(Form)
        self.button_2.setObjectName(u"button_2")
        self.button_2.setGeometry(QRect(180, 380, 141, 41))
        self.select_file = QPushButton(Form)
        self.select_file.setObjectName(u"select_file")
        self.select_file.setGeometry(QRect(30, 20, 141, 41))

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.button.setText(QCoreApplication.translate("Form", u"PushButton", None))
        self.button_2.setText(QCoreApplication.translate("Form", u"PushButton", None))
        self.select_file.setText(QCoreApplication.translate("Form", u"\u9009\u62e9\u6587\u4ef6\u76ee\u5f55", None))
    # retranslateUi


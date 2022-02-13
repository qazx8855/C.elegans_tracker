from PySide6.QtWidgets import *
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from main import *

class Window:
    def __init__(self):
        super(Window, self).__init__()
        # 从ui文件中加载UI定义
        qfile = QFile("demo1.ui")
        qfile.open(QFile.ReadOnly)
        qfile.close()
        # 从UI定义中动态创建一个相应的窗口对象
        self.ui = QUiLoader().load(qfile)

        # 信号处理
        self.ui.button.clicked.connect(self.btnClick)
        # self.button.clicked.connect(self.btnClick)

        self.model = Model()


    def btnClick(self):
        info = self.ui.textEdit.toPlainText()  # 获取文本信息
        # info = self.textEdit.toPlainText()
        print(info)


if __name__ == '__main__':
    app = QApplication([])
    # app.setWindowIcon(QIcon("logo.png"))    # 添加图标
    w = Window()
    w.ui.show()
    # w.win.show()
    app.exec()

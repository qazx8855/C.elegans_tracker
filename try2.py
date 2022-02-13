def __init__(self, MainWindow):
    super(MyWindow, self).__init__()
    self.setupUi(MainWindow)
    self._translate = QCoreApplication.translate  # 对self._translate("MainWindow", "关闭摄像头")的_translate初始化
    self.detect.clicked.connect(self.show_message)
    self.timer_camera = QTimer(self)  # 实时刷新，不然视频不动态显示
    self.timer_camera.timeout.connect(self.start_camera)  # 连接到显示的槽函数，以上两步要在初始化中完成，**注意：timer_camera是对应的定时器函数**
    self.cap = cv2.VideoCapture(0)  # 打开摄像头，在初始化中完成


def show_message(self):
    self.detect.setText(self._translate("MainWindow", "关闭摄像头"))
    self.timer_camera.start(
        0.01)  # 先按下detect按钮，连接此槽函数，开启实时检测，再在初始化中设置开启实时检测需要连接的槽函数。如果把这行命令放在初始化当中，则程序一运行就会打开摄像头。是在按下了按钮之后，启动定时器，定时结束，触发图像显示事件


def start_camera(self):  # 在detect按钮按下后，打开摄像头，实时读取图像并显示到界面的QLable中。
    ret, img = self.cap.read()
    height, width, depth = img.shape
    im = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 转成RGB
    im = QImage(im.data, width, height,
                width * depth, QImage.Format_RGB888)  # 对读取到的im进行转换
    self.img_show.setPixmap(QPixmap.fromImage(im))  # 用QPixmap.fromImage函数把im转换成可以放到QLable上的类型。


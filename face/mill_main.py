import datetime
import json
import os
import platform
import sys
import threading
import face_recognition as fr

import cv2
import numpy as np
import qimage2ndarray as qimage2ndarray
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QImage, QScreen, qRed, qGreen, qBlue
from PyQt5.QtWidgets import QDialog, QMessageBox, QApplication, QVBoxLayout, QWidget, QMainWindow
from PyQt5.uic import loadUi

from face.mill_faceDB import access_db


class layout_main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window = QtWidgets.QWidget()
        self.layout = QtWidgets.QGridLayout()
        self.setCentralWidget(self.window)
        self.window.setLayout(self.layout)
        self.setFixedSize(640, 480)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 처음시작
        self.layout.addWidget(layout_start(self), 0, 0)

        # config.json 값 설정용

        self.cam_num = 0
        self.cam_cap = 0



        self.cam_dev = 0
        self.cam_cap = 0
        self.distance = 0
        self.viewROI = False
        self.viewFPS = False
        self.width = 0
        self.height = 0
        self.log = False
        self.run = False
        self.image = None

        self.init()

    def init(self):
        # config json file read
        with open('config.json') as json_file:
            setting = json.load(json_file)

        # ---------------------------------------camera setting---------------------------------------------
        for s_os in setting["camera"]["os"]:
            if s_os in platform.platform():
                self.cam_num = setting["camera"]["os"][s_os]["dev"]
                self.cam_cap = setting["camera"]["os"][s_os]["cap"]
                break



        # ROI size
        self.width = setting["camera"]["roi"]["width"]
        self.height = setting["camera"]["roi"]["height"]
        self.cap_size = (self.width, self.height)

        # debug용
        self.viewROI = setting["view"]["roi"]
        self.viewFPS = setting["view"]["fps"]

        pass


    def move_start(self):
        self.layout.addWidget(layout_start(self), 0, 0)

    def move_capture(self):
        self.layout.addWidget(layout_capture(self), 0, 0)

    def move_recognition(self):
        self.layout.addWidget(layout_recognition(self), 0, 0)


class layout_start(QWidget):
    def __init__(self, parent):
        super(layout_start, self).__init__(parent)
        loadUi('layout/start.ui', self)
        self.parent = parent

        self.btn_capture.clicked.connect(self.click_capture)
        self.btn_recognition.clicked.connect(self.click_recognition)

    def click_capture(self):
        self.deleteLater()
        self.parent.move_capture()

    def click_recognition(self):
        self.deleteLater()
        self.parent.move_recognition()

class layout_capture(QWidget):
    def __init__(self, parent):
        super(layout_capture, self).__init__(parent)
        loadUi('layout/capture.ui', self)
        self.parent = parent

        self.btn_save.clicked.connect(self.click_save)
        self.btn_back.clicked.connect(self.click_back)

        self.take_photo = Take_photo()
        self.take_photo.start()
        self.take_photo.ImageUpdate.connect(self.ImageUpdateSlot)



        # config json file read
        with open('config.json') as json_file:
            setting = json.load(json_file)

        # ROI size
        self.width = setting["camera"]["roi"]["width"]
        self.height = setting["camera"]["roi"]["height"]
        self.cap_size = (self.width, self.height)


    def click_save(self):

        if self.et_name.text() == "":
            msg = QMessageBox()
            msg.setWindowFlag(Qt.WindowStaysOnTopHint)
            msg.setText('이름을 입력해주세요.')
            msg.setStandardButtons(QMessageBox.Yes)
            x = msg.exec_()
            if x == QMessageBox.Yes:
                return


        self.take_photo.stop()
        # self.imgLabel.pixmap().save("tmp.jpg")

        msg = QMessageBox()
        msg.setWindowFlag(Qt.WindowStaysOnTopHint)
        msg.setIconPixmap(QPixmap(self.imgLabel.pixmap()))
        msg.setText('저장 하시겠습니까?')
        msg.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        x = msg.exec_()
        if x == QMessageBox.Yes:
            name = self.et_name.text()
            captured_img = "tmp/" + name + "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"

            tmp = self.imgLabel.pixmap().toImage()
            frame = qimage2ndarray.rgb_view(tmp)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_crop = fr.face_locations(frame)
            frame = frame[face_crop[0][0]:face_crop[0][2], face_crop[0][3]:face_crop[0][1]]
            if not os.path.isdir("tmp"):
                os.mkdir("tmp")
            cv2.imwrite(captured_img, frame)


            _, _, col, error_col = access_db()
            with open(captured_img, "rb") as data:
                photo = data.read()
            # os.remove(captured_img)
            try:
                id = fr.face_encodings(fr.load_image_file(captured_img), model='large')[0]
                data = {'name': name, 'id': id.tolist(), 'photo': photo}
                col.insert_one(data)
                print('저장 완료!! : ', name)
                self.take_photo.start()
            except IndexError:
                error_col.insert_one({'name': name})
                os.remove(captured_img)
                print('warning! face not detected! : ', name)
            # client.close()
        else: pass


    def click_back(self):
        self.take_photo.stop()
        self.deleteLater()
        self.parent.move_start()

    def ImageUpdateSlot(self, Image):
        self.imgLabel.setPixmap(QPixmap.fromImage(Image))
        self.imgLabel.setScaledContents(True)



class Take_photo(QThread):
    ImageUpdate = pyqtSignal(QImage)
    def run(self):
        self.ThreadActive = True

        with open('config.json') as json_file:
            setting = json.load(json_file)

        for s_os in setting["camera"]["os"]:
            if s_os in platform.platform():
                cam_num = setting["camera"]["os"][s_os]["dev"]
                cam_cap = setting["camera"]["os"][s_os]["cap"]
                break

        cap = cv2.VideoCapture(cam_num, cam_cap)
        while self.ThreadActive:
            ret, frame = cap.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame, 1)
            img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            self.ImageUpdate.emit(img)

    def stop(self):
        self.ThreadActive = False
        self.quit()




class layout_recognition(QWidget):
    def __init__(self, parent):
        super(layout_recognition, self).__init__(parent)
        loadUi('layout/recognition.ui', self)
        self.parent = parent

        self.btn_back.clicked.connect(self.click_back)


    def click_back(self):
        self.deleteLater()
        self.parent.move_start()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    myWindow = layout_main()

    myWindow.show()
    app.exec_()




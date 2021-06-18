import datetime
import json
import multiprocessing
import os
import platform
import sys
import time
import tkinter.messagebox
from multiprocessing import Process, Queue

import cv2
import face_recognition as fr
import numpy as np
import qimage2ndarray as qimage2ndarray
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMessageBox, QApplication, QWidget, QMainWindow
from PyQt5.uic import loadUi

from face.mill_faceDB import access_db


class layout_main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window = QtWidgets.QWidget()
        self.layout = QtWidgets.QGridLayout()
        self.setCentralWidget(self.window)
        self.window.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
        # self.showFullScreen()#전체화면
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

        self.take_Capture = takeCapture()
        self.take_Capture.start()
        self.take_Capture.ImageUpdate.connect(self.ImageUpdateSlot)

    def click_save(self):
        if self.et_name.text() == "":
            msg = QMessageBox()
            msg.setWindowFlag(Qt.WindowStaysOnTopHint)
            msg.setText('이름을 입력해주세요.')
            msg.setStandardButtons(QMessageBox.Yes)
            x = msg.exec_()
            if x == QMessageBox.Yes:
                return

        self.take_Capture.terminate()
        # self.imgLabel.pixmap().save("tmp.jpg")

        msg = QMessageBox()
        msg.setWindowFlag(Qt.WindowStaysOnTopHint)

        #메세지에 띄울 사각테두리 체크된 이미지 처리
        tmp1 = QImage.copy(self.imgLabel.pixmap().toImage())
        frame1 = qimage2ndarray.rgb_view(tmp1)
        frame2 = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
        face_crop = fr.face_locations(frame2)

        # 에러메세지 출력해야됨------------------------------------------
        if len(face_crop) == 0:
            print("인식못함")
            self.take_Capture.start()
            return
        elif len(face_crop) > 1:
            print("여러개 인식됨")
            self.take_Capture.start()
            return
        face_crop = face_crop[0]
        tmp1 = np.copy(frame1)
        cv2.rectangle(tmp1,
                      (face_crop[3], face_crop[0]),
                      (face_crop[1], face_crop[2]),
                      (0, 0, 255), 2)



        # msg.setIconPixmap(self.imgLabel.pixmap())
        msg.setIconPixmap(QPixmap.fromImage(QImage(tmp1.data, tmp1.shape[1], tmp1.shape[0], QImage.Format_RGB888)))
        msg.setText('저장 하시겠습니까?')
        msg.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        x = msg.exec_()
        if x == QMessageBox.Yes:
            name = self.et_name.text()
            captured_img = "tmp/" + name + "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"

            tmp = self.imgLabel.pixmap().toImage()
            frame = qimage2ndarray.rgb_view(tmp)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            frame = frame[face_crop[0]:face_crop[2], face_crop[3]:face_crop[1]]
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

            except IndexError:
                error_col.insert_one({'name': name})
                # os.remove(captured_img)
                print('warning! face not detected! : ', name)
            # client.close()
        else:
            pass
        # capture restart
        self.take_Capture.start()


    def ImageUpdateSlot(self, Image):
        self.imgLabel.setPixmap(QPixmap.fromImage(Image))
        self.imgLabel.setScaledContents(True)

    def click_back(self):
        self.take_Capture.terminate()
        self.deleteLater()
        self.parent.move_start()

class takeCapture(QThread):
    ImageUpdate = pyqtSignal(QImage)

    def run(self):
        self.ThreadActive = True

        while self.ThreadActive:
            ret, frame = cap.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame, 1)
            img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            self.ImageUpdate.emit(img)



class layout_recognition(QWidget):
    def __init__(self, parent):
        super(layout_recognition, self).__init__(parent)
        loadUi('layout/recognition.ui', self)
        self.parent = parent

        image_anlyizeActive = True
        self.take_Recognition = takeRecognition()
        self.take_Recognition.start()
        self.take_Recognition.ImageUpdate.connect(self.ImageUpdateSlot)




        self.btn_back.clicked.connect(self.click_back)





    def ImageUpdateSlot(self, Image):
        self.imgLabel.setPixmap(QPixmap.fromImage(Image))
        self.imgLabel.setScaledContents(True)

    def click_back(self):
        self.take_Recognition.terminate()
        self.deleteLater()
        self.parent.move_start()


class takeRecognition(QThread):
    ImageUpdate = pyqtSignal(QImage)

    def run(self):
        self.RecognitionActive = True

        cap_size = (setting["camera"]["roi"]["width"], setting["camera"]["roi"]["height"])
        s = time.time()
        while self.RecognitionActive:
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
            # cpu 코어 갯수 - 2개 만큼만 face_recognition돌림
            # capture돌아가는 1개
            # 여유분 1개
            if q.qsize() < multiprocessing.cpu_count() - 2:
                seconds = time.time() - s
                if seconds > float(1) / (multiprocessing.cpu_count() - 2):
                    s = time.time()
                    # ROI
                    # 중앙에서 cap_size만큼
                    q.put(frame[int(frame.shape[1] / 2 - cap_size[1] / 2): int(frame.shape[1] / 2 + cap_size[1] / 2),
                          int(frame.shape[0] / 2 - cap_size[0] / 2): int(frame.shape[0] / 2 + cap_size[0] / 2)])

            fps = 0
            try:
                pass
                # calculate fps
                fps = 1 / seconds
                fps = ("%.2f" % fps)
            # print(f"fps : {fps}", '\n')
            except:
                pass

            # ROI
            if setting["view"]["roi"]:
                cv2.imshow('roi',
                           frame[int(frame.shape[0] / 2 - cap_size[0] / 2): int(frame.shape[0] / 2 + cap_size[0] / 2),
                           int(frame.shape[1] / 2 - cap_size[1] / 2): int(frame.shape[1] / 2 + cap_size[1] / 2)])

            # ROI사각형
            cv2.rectangle(frame,
                          (int(frame.shape[1] / 2 - cap_size[1] / 2), int(frame.shape[0] / 2 - cap_size[0] / 2)),
                          (int(frame.shape[1] / 2 + cap_size[1] / 2), int(frame.shape[0] / 2 + cap_size[0] / 2)),
                          (0, 0, 255), 2)
            # fps출력
            if setting["view"]["fps"]:
                cv2.putText(frame, "fps : " + str(fps), (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            self.ImageUpdate.emit(img)








with open('config.json') as json_file:
    setting = json.load(json_file)

for s_os in setting["camera"]["os"]:
    if s_os in platform.platform():
        cam_num = setting["camera"]["os"][s_os]["dev"]
        cam_cap = setting["camera"]["os"][s_os]["cap"]
        break

cap = cv2.VideoCapture(cam_num, cam_cap)
q = Queue()
pro_list = []

_, _, col, error_col = access_db()
n = list(col.find({}))
names = [i['name'] for i in n]
id = [j['id'] for j in n]





def image_anlyize(q):

    while True:
        # 큐에 있는 frame가져와서 face_location처리
        if q:
            frame = q.get()
            face_locations = fr.face_locations(frame)
            if face_locations:
                face_encodings = fr.face_encodings(frame, face_locations)

                for fe in face_encodings:
                    name = "- - -"
                    face_distances = fr.face_distance(id, fe)
                    best_match_index = np.argmin(face_distances)
                    if face_distances[best_match_index] < setting["distance"]:
                        name = names[best_match_index]
                    print(name)

if __name__ == '__main__':
    for _ in range(multiprocessing.cpu_count() - 1):
        p = Process(target=image_anlyize, args=(q,))
        pro_list.append(p)
        p.start()
        time.sleep(float(1) / (multiprocessing.cpu_count() - 2))
    app = QApplication(sys.argv)
    myWindow = layout_main()

    myWindow.show()
    app.exec_()

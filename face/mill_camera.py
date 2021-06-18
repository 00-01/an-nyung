import multiprocessing
import platform
import time
from multiprocessing import Process, Queue

import cv2
import face_recognition as fr
import numpy as np

from db import access_db


class camera():
    def __init__(self):
        super(camera, self).__init__()
        self.pro_list = []  # 얼굴 탐색 멀티 프로세스 리스트
        self.q = None

        # config.json 값 설정용
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

    def init(self, setting):

        # ---------------------------------------release---------------------------------------------
        self.release()

        # ---------------------------------------camera setting---------------------------------------------
        for s_os in setting["camera"]["os"]:
            if s_os in platform.platform():
                self.cam_num = setting["camera"]["os"][s_os]["dev"]
                self.cam_cap = setting["camera"]["os"][s_os]["cap"]
                break

        self.cap = cv2.VideoCapture(self.cam_num, self.cam_cap)
        self.cap_size = (self.width, self.height)

        # ROI size
        self.width = setting["camera"]["roi"]["width"]
        self.height = setting["camera"]["roi"]["height"]

        # debug용
        self.viewROI = setting["view"]["roi"]
        self.viewFPS = setting["view"]["fps"]

        # ---------------------------------------distance setting---------------------------------------------
        self.distance = setting["distance"]

        # ---------------------------------------debug---------------------------------------------
        debug = setting["debug"]
        if debug:
            self.log = True
            self.viewROI = True
            self.viewFPS = True

        self.run = True

    def release(self):
        self.run = False
        for pp in self.pro_list:
            pp.kill()
        cv2.destroyAllWindows()
        self.pro_list = []

    def search_Face(self):
        q = Queue()
        # multiProcess execute
        for _ in range(multiprocessing.cpu_count() - 1):
            p = Process(target=camera().image_anlyize, args=(q, self.distance,))
            self.pro_list.append(p)
            p.start()
            time.sleep(float(1) / (multiprocessing.cpu_count() - 2))

        s = time.time()
        while self.run:
            ret, frame = self.cap.read()
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
                    q.put(frame[int(frame.shape[1] / 2 - self.cap_size[1] / 2): int(
                        frame.shape[1] / 2 + self.cap_size[1] / 2),
                          int(frame.shape[0] / 2 - self.cap_size[0] / 2): int(
                              frame.shape[0] / 2 + self.cap_size[0] / 2)])

            fps = 0
            try:
                pass
                # calculate fps
                fps = 1 / seconds
                fps = ("%.2f" % fps)
            # print(f"fps : {fps}", '\n')
            except:
                fps = "0"
                pass

            # ROI
            if self.viewROI:
                cv2.imshow('roi',
                           frame[int(frame.shape[0] / 2 - self.cap_size[0] / 2): int(
                               frame.shape[0] / 2 + self.cap_size[0] / 2),
                           int(frame.shape[1] / 2 - self.cap_size[1] / 2): int(
                               frame.shape[1] / 2 + self.cap_size[1] / 2)])

            # ROI사각형 테두리 그리기
            cv2.rectangle(frame,
                          (int(frame.shape[1] / 2 - self.cap_size[1] / 2),
                           int(frame.shape[0] / 2 - self.cap_size[0] / 2)),
                          (int(frame.shape[1] / 2 + self.cap_size[1] / 2),
                           int(frame.shape[0] / 2 + self.cap_size[0] / 2)),
                          (0, 0, 255), 2)
            # fps출력
            if self.viewFPS:
                cv2.putText(frame, "fps : " + fps, (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

            cv2.imshow('frame', frame)

            if cv2.waitKey(1) == 27:
                self.cap.release()
                return

    def image_anlyize(self, q, distance):
        _, _, col, error_col = access_db()
        n = list(col.find({}))
        names = [i['name'] for i in n]
        id = [j['id'] for j in n]
        while self.run:
            frame = q.get()
            face_locations = fr.face_locations(frame)
            if face_locations:
                face_encodings = fr.face_encodings(frame, face_locations)
                for (y, x1, y1, x), face_encoding in zip(face_locations, face_encodings):
                    name = "- - -"
                    face_distances = fr.face_distance(id, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if face_distances[best_match_index] < distance:
                        name = names[best_match_index]
                        print(name)

    def register_face(self):
        print("run thread_reg")
        self.run = True
        t = multiprocessing.Process(target=self.thread_register_face)
        t.start()

    def thread_register_face(self):
        cap = cv2.VideoCapture(0, 0)
        cap_size = (300, 300)
        while True:
            print("running thread_reg")
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
            frame = frame[int(frame.shape[1] / 2 - cap_size[1] / 2): int(
                frame.shape[1] / 2 + cap_size[1] / 2),
                    int(frame.shape[0] / 2 - cap_size[0] / 2): int(
                        frame.shape[0] / 2 + cap_size[0] / 2)]

            cv2.imshow('frame', frame)
            if cv2.waitKey(1) == 27:
                pass

import datetime
import json
import multiprocessing
import os
import platform
import threading
import time
import tkinter as tk
from multiprocessing import Queue, Process
from datetime import datetime
import cv2
import face_recognition as fr
import numpy as np
from PIL import Image
from PIL import ImageTk

from mill_faceDB import access_db


class layout_controller(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self._frame = None
        self.switch_frame(layout_start)

    # layout switch용
    def switch_frame(self, frame_class):
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.pack()


class layout_start(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        self.background = ImageTk.PhotoImage(file="layout/background.jpg")
        tk.Label(self, image=self.background).pack(side="top")

        tk.Button(self, text="Go to page layout_faceCapture",
                  command=lambda: master.switch_frame(layout_faceCapture)).pack(side="bottom", expand=True, fill="both")
        tk.Button(self, text="Go to page layout_faceRecognition",
                  command=lambda: master.switch_frame(layout_faceRecognition)).pack(side="bottom", expand=True,
                                                                                    fill="both")


class layout_faceCapture(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master
        self.src = None

        # 출력할 이미지 위젯
        self.camera = tk.Label(self)
        self.camera.pack(side="top")

        self.frame = tk.Frame(self)
        self.frame.pack(side="bottom")

        tk.Button(self.frame, text="Save",
                  command=self.click_save).pack(side="left")
        self.name = tk.Entry(self.frame)
        self.name.pack(side="left")
        tk.Button(self.frame, text="Back",
                  command=self.click_back).pack(side="right")

        # 촬영 thread 시작
        self.ThreadCapture = ThreadCapture()
        threading.Thread(target=self.ThreadCapture.run, args=(self,)).start()

    def click_save(self):

        # 이름 설정 안했을 경우 취소
        if len(self.name.get()) == 0:
            return

        # 이미지가져옴>쓰레드 종료>메세지박스>확인,취소>쓰레드재시작
        ret, frame = cam.read()

        # 쓰레드 종료
        self.ThreadCapture.terminate()
        face_crop = fr.face_locations(frame)

        # 얼굴 인식 못할경우 촬영으로 재시작
        if len(face_crop) == 0:
            print("인식못함")
            self.ThreadCapture = ThreadCapture()
            threading.Thread(target=self.ThreadCapture.run, args=(self,)).start()
            return
        elif len(face_crop) > 1:
            print("여러개 인식됨")
            self.ThreadCapture = ThreadCapture()
            threading.Thread(target=self.ThreadCapture.run, args=(self,)).start()
            return

        # 얼굴 인식됨
        face_crop = face_crop[0]
        tmp1 = np.copy(frame)
        cv2.rectangle(tmp1,
                      (face_crop[3], face_crop[0]),
                      (face_crop[1], face_crop[2]),
                      (0, 0, 255), 2)

        # 저장하시겠습니까 메세지 다이얼로그
        btn = SaveCaptureDialog(self, self.name.get() + "으로 저장하시겠습니까?", tmp1).show()
        if btn:
            name = self.name.get()
            captured_img = "tmp/" + name + "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
            # 인식된 이미지(얼굴만)
            frame = frame[face_crop[0]:face_crop[2], face_crop[3]:face_crop[1]]
            if not os.path.isdir("tmp"):
                os.mkdir("tmp")
            cv2.imwrite(captured_img, frame)

            # DB에 넣음
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

            # ------------------------------db새로 불러야됨

        # 촬영 쓰레드 재시작
        self.ThreadCapture = ThreadCapture()
        threading.Thread(target=self.ThreadCapture.run, args=(self,)).start()

        # name widget text 리셋
        self.name.delete(0, 'end')

    def click_back(self):
        self.ThreadCapture.terminate()
        self.master.switch_frame(layout_start)

    def change_img(self, img):  # 레이블의 이미지 변경
        try:
            img = cv2.resize(img, (640, 400))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            self.src = ImageTk.PhotoImage(image=img)
            self.camera.config(image=self.src)
            self.camera.image = self.src
        except:
            pass


class SaveCaptureDialog(tk.Toplevel):
    def __init__(self, parent, msg, img):
        tk.Toplevel.__init__(self, parent)
        # 저장하시겠습니까?
        self.click = False  # OK : True, NO : False

        self.capture = tk.Label(self)
        img = cv2.flip(img, 1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        self.src = ImageTk.PhotoImage(image=img)
        self.capture.config(image=self.src)
        self.capture.image = self.src
        self.capture.pack(side="top")

        tk.Button(self, text="NO", command=self.click_cancel).pack(side="right")
        tk.Button(self, text="OK", command=self.click_ok).pack(side="right")
        tk.Label(self, text=msg).pack(side="right", fill="x")

    def click_ok(self):
        self.click = True
        self.destroy()

    def click_cancel(self):
        self.destroy()

    def show(self):
        self.wm_deiconify()
        self.wait_window()
        return self.click


class ThreadCapture():
    def __init__(self):
        self.flag = True

    def run(self, app):
        self.flag = True
        while self.flag:
            ret, frame = cam.read()
            if ret:
                img = cv2.flip(frame, 1)
                app.change_img(img)
            cv2.waitKey(10)

    def terminate(self):
        self.flag = False

class layout_faceRecognition(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        self.src = None

        # 출력할 이미지 위젯
        self.camera = tk.Label(self)
        self.camera.pack(side="top")

        self.frame = tk.Frame(self)
        self.frame.pack(side="bottom")

        tk.Button(self.frame, text="Back",
                  command=self.click_back).pack(side="right")

        # 촬영 thread 시작
        self.ThreadRecognition = ThreadRecognition()
        threading.Thread(target=self.ThreadRecognition.run, args=(self,)).start()

    def click_back(self):
        self.ThreadRecognition.terminate()
        self.master.switch_frame(layout_start)

    def change_img(self, img):  # 레이블의 이미지 변경
        try:
            img = cv2.resize(img, (640, 400))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            self.src = ImageTk.PhotoImage(image=img)
            self.camera.config(image=self.src)
            self.camera.image = self.src
        except:
            pass


class ThreadRecognition():
    def __init__(self):
        self.flag = True

    def run(self, app):
        self.flag = True

        for process in pro_list:
            process.kill()

        for _ in range(multiprocessing.cpu_count() - 1):
            p = Process(target=image_anlyize, args=(q,result,))
            pro_list.append(p)
            p.start()

        start_time = time.time()
        delay_time = time.time()
        while self.flag:
            # 얼굴 인식 멀티 프로세스가 덜열려있는지 체크해서 계속 숫자 맞춰줌
            if len(pro_list) < multiprocessing.cpu_count():
                p = Process(target=image_anlyize, args=(q,result))
                pro_list.append(p)
                p.start()
                
                
            ret, frame = cam.read()
            if ret:
                frame = cv2.flip(frame, 1)
                # cpu 코어 갯수 - 2개 만큼만 face_recognition돌림
                # capture돌아가는 1개
                # 여유분 1개
                if q.qsize() < multiprocessing.cpu_count() - 2:
                    dif_time = time.time() - start_time
                    if dif_time > float(1) / (multiprocessing.cpu_count() - 2):
                        start_time = time.time()
                        # ROI
                        # 중앙에서 cap_size만큼
                        q.put(
                            frame[int(frame.shape[1] / 2 - cap_size[1] / 2): int(frame.shape[1] / 2 + cap_size[1] / 2),
                            int(frame.shape[0] / 2 - cap_size[0] / 2): int(frame.shape[0] / 2 + cap_size[0] / 2)])

                fps = 0
                try:
                    pass
                    # calculate fps
                    fps = 1 / dif_time
                    fps = ("%.2f" % fps)
                # print(f"fps : {fps}", '\n')
                except:
                    pass

                # ROI
                if setting["view"]["roi"]:
                    cv2.imshow('roi',
                               frame[
                               int(frame.shape[0] / 2 - cap_size[0] / 2): int(frame.shape[0] / 2 + cap_size[0] / 2),
                               int(frame.shape[1] / 2 - cap_size[1] / 2): int(frame.shape[1] / 2 + cap_size[1] / 2)])

                # ROI사각형
                cv2.rectangle(frame,



                              (int(frame.shape[1] / 2 - cap_size[1] / 2), int(frame.shape[0] / 2 - cap_size[0] / 2)),
                              (int(frame.shape[1] / 2 + cap_size[1] / 2), int(frame.shape[0] / 2 + cap_size[0] / 2)),
                              (0, 0, 255), 2)
                # fps출력
                if setting["view"]["fps"]:
                    cv2.putText(frame, "fps : " + str(fps), (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1,
                                cv2.LINE_AA)

                app.change_img(frame)

            cv2.waitKey(10)
            if time.time() - delay_time > 1:
                if result.qsize() > 3:
                    ls = []
                    print("=============================start")
                    for q_result in range(result.qsize()):
                        ls.append(result.get())
                    print(ls)
                    print("선택결과 : ", end="")
                    print(max(ls, key=ls.count))
                    print("=============================end")
                    delay_time = time.time()

    def terminate(self):
        self.flag = False
        for process in pro_list:
            process.kill()

_, _, col, error_col = access_db()
n = list(col.find({}))
names = [i['name'] for i in n]
id = [j['id'] for j in n]


def image_anlyize(q, result):
    # 멀티프로세스는 30초동안 인식된 얼굴 안들어오면 자동 종료됨
    count = 0
    while True:
        # 큐에 있는 frame가져와서 face_location처리
        if q.qsize() != 0:
            frame = q.get()
            face_locations = fr.face_locations(frame)
            if len(face_locations) == 1:
                count = 0
                face_encodings = fr.face_encodings(frame, face_locations)
                for fe in face_encodings:
                    name = "- - -"
                    face_distances = fr.face_distance(id, fe)
                    best_match_index = np.argmin(face_distances)
                    if face_distances[best_match_index] < setting["distance"]:
                        name = names[best_match_index]
                    result.put(name)
                    # print(name)
            elif len(face_locations) == 0:
                count += 1
                if count > 20:
                    print('종료합니다.')
                    exit()
                time.sleep(0.5)


with open('config.json') as json_file:
    setting = json.load(json_file)

for s_os in setting["camera"]["os"]:
    if s_os in platform.platform():
        cam_num = setting["camera"]["os"][s_os]["dev"]
        cam_cap = setting["camera"]["os"][s_os]["cap"]
        break

# 카메라 전역변수
cam = cv2.VideoCapture(cam_num, cam_cap)
cap_size = (setting["camera"]["roi"]["width"], setting["camera"]["roi"]["height"])

q = Queue()
result = Queue()
pro_list = []


if __name__ == "__main__":
    if setting["log"]:
        print("cpu_count : " + str(multiprocessing.cpu_count()))
        print("cam connected : " + str(cam.isOpened()))

    # 기존에 실행되던 process종료해야됨(python3) 본인뺴고
    # os별로 명령어가 다름
    # os.system("killall -9 python3")

    # for _ in range(multiprocessing.cpu_count() - 1):
    #     p = Process(target=image_anlyize, args=(q,))
    #     pro_list.append(p)
    #     p.start()
    #     time.sleep(float(1) / (multiprocessing.cpu_count() - 2))

    app = layout_controller()
    app.mainloop()

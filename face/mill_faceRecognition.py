import datetime
import json
import multiprocessing
import os
import platform
import threading
import time
import tkinter as tk
from datetime import datetime
from multiprocessing import Queue, Process
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

    def programExit(self):
        if processFlag.qsize() != 0:
            processFlag.get()

        if self._frame != None:
            self._frame.programExit()
        if q.qsize() != 0:
            for _ in range(q.qsize()):
                q.get()
        if result.qsize() != 0:
            for _ in range(result.qsize()):
                result.get()
        cam.release()

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
    def programExit(self):
        pass

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

    def programExit(self):
        self.ThreadCapture.terminate()

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
            logShow("no search face location")
            self.ThreadCapture = ThreadCapture()
            threading.Thread(target=self.ThreadCapture.run, args=(self,)).start()
            return
        elif len(face_crop) > 1:
            logShow("more 2 search face location")
            self.ThreadCapture = ThreadCapture()
            threading.Thread(target=self.ThreadCapture.run, args=(self,)).start()
            return

        logShow("1 search face location")
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
            captured_img = "tmp/" + name + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
            # 인식된 이미지(얼굴만)
            frame = frame[face_crop[0]:face_crop[2], face_crop[3]:face_crop[1]]
            if not os.path.isdir("tmp"):
                os.mkdir("tmp")
            cv2.imwrite(captured_img, frame)
            logShow("save img file name : " + captured_img)

            # DB에 넣음
            _, _, col, error_col = access_db()
            with open(captured_img, "rb") as data:
                photo = data.read()
                logShow("load db")
            # os.remove(captured_img)
            try:
                id = fr.face_encodings(fr.load_image_file(captured_img), model='large')[0]
                data = {'name': name, 'id': id.tolist(), 'photo': photo}
                col.insert_one(data)

                # name widget text 리셋
                self.name.delete(0, 'end')

                logShow("save new db : " + name)

            except IndexError:
                error_col.insert_one({'name': name})
                # os.remove(captured_img)
                print('warning! face not detected! : ', name)
                logShow("save new db error" + name)

            # ------------------------------db새로 불러야됨--------------------------------------------------------------------

        # 촬영 쓰레드 재시작
        self.ThreadCapture = ThreadCapture()
        threading.Thread(target=self.ThreadCapture.run, args=(self,)).start()


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
        logShow("ThreadCapture Thread terminate")


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

    def programExit(self):
        self.ThreadRecognition.terminate()

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
        logShow("ThreadRecognition Thread run")
        self.flag = True
        start_time = time.time()
        delay_time = time.time()
        while self.flag:
            ret, frame = cam.read()
            if ret:
                frame = cv2.flip(frame, 1)
                # cpu 코어 갯수 - 2개 만큼만 face_recognition돌림
                # video capture돌아가는 1개
                # UI cs 1개
                if q.qsize() < core_count:
                    dif_time = time.time() - start_time
                    if dif_time > float(1) / (core_count):
                        start_time = time.time()
                        # ROI
                        # 중앙에서 cap_size만큼
                        q.put(
                            frame[int(frame.shape[1] / 2 - cap_size[1] / 2): int(frame.shape[1] / 2 + cap_size[1] / 2),
                            int(frame.shape[0] / 2 - cap_size[0] / 2): int(frame.shape[0] / 2 + cap_size[0] / 2)])
                        logShow("insert q")

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
                ls = []
                for q_result in range(result.qsize()):
                    ls.append(result.get())
                if len(ls) != 0:
                    logShow("=============================")
                    logShow("list : " + " ".join(ls))
                    logShow("choice : " + max(ls, key=ls.count))
                    logShow("=============================")
                    delay_time = time.time()

    def terminate(self):
        self.flag = False
        logShow("ThreadRecognition Thread terminate")



_, _, col, error_col = access_db()
n = list(col.find({}))
names = [i['name'] for i in n]
id = [j['id'] for j in n]


def image_anlyize(i, q, result, processFlag):
    logShow(str(i) + " process enter")
    while processFlag.qsize() != 0:
        # 큐에 있는 frame가져와서 face_location처리
        if q.qsize() != 0:
            frame = q.get()
            logShow(str(i) + " process face_locations start")
            face_locations = fr.face_locations(frame)
            logShow(str(i) + " process face_locations end")
            if len(face_locations) == 1:
                logShow(str(i) + " process face_encodings start")
                face_encodings = fr.face_encodings(frame, face_locations)
                logShow(str(i) + " process face_encodings end")
                for fe in face_encodings:
                    name = "- - -"
                    face_distances = fr.face_distance(id, fe)
                    best_match_index = np.argmin(face_distances)
                    if face_distances[best_match_index] < setting["distance"]:
                        name = names[best_match_index]
                    logShow(str(i) + " DB search end")
                    result.put(name)
                    # print(name)
        elif q.qsize() == 0:
            time.sleep(float(1) / (core_count))

    logShow(str(i) + " process end")


with open('config.json') as json_file:
    setting = json.load(json_file)

for s_os in setting["camera"]["os"]:
    if s_os in platform.platform():
        cam_num = setting["camera"]["os"][s_os]["dev"]
        cam_cap = setting["camera"]["os"][s_os]["cap"]
        break

# face_recognition에 쓸 코어 갯수
try:
    core_count = setting["core"]
except:
    core_count = multiprocessing.cpu_count() - 2

# 로그작업 유무
try:
    log = setting["log"]
    log = True
except:
    log = False

def logShow(string):
    if log:
        lg = open(datetime.now().strftime("%Y%m%d_") + setting["log"] + ".txt", "a")
        lg.write(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " :::: {}\n".format(string))
    print(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " :::: ", end="")
    print(string)


# 카메라 전역변수
cam = cv2.VideoCapture(cam_num, cam_cap)
cap_size = (setting["camera"]["roi"]["width"], setting["camera"]["roi"]["height"])

q = Queue()
result = Queue()
processFlag = Queue()
pro_list = []
app = layout_controller()

def programExit():
    app.programExit()
    app.destroy()

if __name__ == "__main__":
    logShow("start main")
    logShow("cpu_count : " + str(core_count))
    logShow("camera connected : " + str(cam.isOpened()))

    processFlag.put("1")
    for i in range(core_count):
        logShow(str(i) + " process start")
        p = Process(target=image_anlyize, args=(i, q, result, processFlag, ))
        pro_list.append(p)
        p.start()

    app.protocol("WM_DELETE_WINDOW", programExit)
    app.mainloop()

    for i in range(len[pro_list]):
        logShow(str(i) + " process kill")
        pro_list[i].kill()



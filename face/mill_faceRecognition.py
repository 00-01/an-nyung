import datetime
import json
import multiprocessing
import os
import platform
import threading
import time
import tkinter as tk
from datetime import datetime
from multiprocessing import Process

import cv2
import face_recognition as fr
import numpy as np
from PIL import Image
from PIL import ImageTk

from mill_faceDB import mill_faceDB


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
        self._frame.pack(fill="both", expand=True)

    def programExit(self):
        if self._frame is not None:
            self._frame.programExit()

        cam.release()


class layout_start(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        img = Image.open("layout/background.jpg")
        # img = img.resize((master.winfo_screenwidth(), master.winfo_screenheight()), Image.ANTIALIAS)
        self.background = ImageTk.PhotoImage(img)
        # background = tk.Canvas(self, bd=0, highlightthickness=0)
        # background.pack(fill="both", expand=True)
        # background.create_image(0, 0, image=self.background)
        # background.create_text(150, 100, text="테스트입니다.", font=("나눔고딕코딩",20), fill="red")

        tk.Label(self, image=self.background).pack(side="top", expand="true", fill="both")

        tk.Button(self, text="Go to page layout_faceCapture",
                  command=lambda: master.switch_frame(layout_faceCapture)).pack(side="bottom", fill="both")
        tk.Button(self, text="Go to page layout_faceRecognition",
                  command=lambda: master.switch_frame(layout_faceRecognition)).pack(side="bottom", fill="both")

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
            time.sleep(0.5)

            # DB에 넣음
            with open(captured_img, "rb") as data:
                photo = data.read()
                logShow("load db")
            # os.remove(captured_img)
            try:
                _, _, col, error_col, names, id = mill_faceDB().access_db()
                id = fr.face_encodings(fr.load_image_file(captured_img), model='large')[0]
                data = {'name': name, 'id': id.tolist(), 'photo': photo}
                col.insert_one(data)

                # name textbox text 리셋
                self.name.delete(0, 'end')
                logShow("save new db : " + name)

            except IndexError:
                error_col.insert_one({'name': name})
                # os.remove(captured_img)
                print('warning! face not detected! : ', name)
                logShow("save new db error" + name)

        # 촬영 쓰레드 재시작
        self.ThreadCapture = ThreadCapture()
        threading.Thread(target=self.ThreadCapture.run, args=(self,)).start()

    def click_back(self):
        self.ThreadCapture.terminate()
        self.master.switch_frame(layout_start)

    def change_img(self, img):  # 레이블의 이미지 변경
        try:
            # img = cv2.resize(img, (640, 400))
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

        self.information = tk.Label(self)
        self.information.pack(side="top")

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
        shareResource["imageAnalizeFlag"] = 0
        self.ThreadRecognition.terminate()

    def click_back(self):
        shareResource["imageAnalizeFlag"] = 2
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
        shareResource["imageAnalizeFlag"] = 4
        logShow("ThreadRecognition Thread run")
        self.flag = True
        motionFlag = True
        motionFrameCount = 0
        motionOriginImage = None
        start_time = time.time()
        delay_time = time.time()
        display_time = time.time()
        information_time = time.time()
        while self.flag:
            if len(app.information.cget("text")) != 0:
                if time.time() - information_time > setting["information"]:
                    app.information.config(text="")
            ret, frame = cam.read()
            if ret:
                # motion detect
                motionFrameCount += 1
                if motionOriginImage is None:
                    motionOriginImage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                motionCompareImage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                mse_value = np.sum((motionOriginImage - motionCompareImage) ** 2) / float(motionOriginImage.size)

                if mse_value > 30:
                    # cv2.imshow("origin", motionOriginImage)
                    # cv2.imshow("compare", motionCompareImage)
                    motionFlag = True
                    if shareResource["imageAnalizeFlag"] == 2:
                        shareResource["imageAnalizeFlag"] = 1
                    display_time = time.time()

                if motionFrameCount > 10:
                    motionFrameCount = 0
                    motionOriginImage = motionCompareImage

                if time.time() - display_time > setting["displayOut"] and motionFlag:
                    logShow("displayOut")
                    motionFlag = False
                    shareResource["imageAnalizeFlag"] = 2

                    aaa = np.copy(frame)
                    aaa[:] = 0
                    cv2.putText(aaa, "displayOut", (0, 40), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 1,
                                cv2.LINE_AA)
                    app.change_img(aaa)

                if not motionFlag:
                    continue
                # ---------------------------------------light

                frame = cv2.flip(frame, 1)
                # cpu 코어 갯수 - 2개 만큼만 face_recognition돌림
                # video capture돌아가는 1개
                # UI cs 1개
                if captureFrame.qsize() < core_count and time.time() - start_time > float(1) / core_count:
                    start_time = time.time()
                    # ROI
                    # 중앙에서 cap_size만큼
                    captureFrame.put(
                        frame[int(frame.shape[0] / 2 - cap_size[1] / 2): int(frame.shape[0] / 2 + cap_size[1] / 2),
                        int(frame.shape[1] / 2 - cap_size[0] / 2): int(frame.shape[1] / 2 + cap_size[0] / 2)])
                    logShow("insert q")
                    continue
                    # q에 들어가는 frame 디버그용
                    # cv2.imshow("q Add", frame[int(frame.shape[0] / 2 - cap_size[1] / 2): int(frame.shape[0] / 2 + cap_size[1] / 2),
                    #     int(frame.shape[1] / 2 - cap_size[0] / 2): int(frame.shape[1] / 2 + cap_size[0] / 2)])
                    # cv2.waitKey(10)

                fps = 0
                try:
                    pass
                    # calculate fps
                    fps = 1 / (time.time() - start_time)
                    fps = ("%.2f" % fps)
                # print(f"fps : {fps}", '\n')
                except:
                    pass

                # ROI
                if setting["view"]["roi"]:
                    cv2.imshow('roi',
                               frame[
                               int(frame.shape[1] / 2 - cap_size[0] / 2): int(frame.shape[0] / 2 + cap_size[1] / 2),
                               int(frame.shape[1] / 2 - cap_size[0] / 2): int(frame.shape[0] / 2 + cap_size[1] / 2)])

                # ROI사각형
                cv2.rectangle(frame,
                              (int(frame.shape[1] / 2 - cap_size[0] / 2), int(frame.shape[0] / 2 - cap_size[1] / 2)),
                              (int(frame.shape[1] / 2 + cap_size[0] / 2), int(frame.shape[0] / 2 + cap_size[1] / 2)),
                              (0, 0, 255), 2)
                # fps출력
                if setting["view"]["fps"]:
                    cv2.putText(frame, "fps : " + str(fps), (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1,
                                cv2.LINE_AA)

                cv2.waitKey(10)
                certification = False
                if time.time() - delay_time > setting["delay"]:
                    print(analizeResult.qsize())
                    if analizeResult.qsize() != 0:
                        ls = []
                        for _ in range(analizeResult.qsize()):
                            ls.append(analizeResult.get())
                        choice = max(ls, key=ls.count)
                        logShow("search list : " + " ".join(ls))
                        logShow("detect name : " + choice)
                        if not debug:
                            print(datetime.now().strftime("%H:%M:%S") + " list : " + " ".join(ls))
                            print(datetime.now().strftime("%H:%M:%S") + " name : " + choice)
                        certification = True

                        # get RFID MODULE
                        app.information.config(text=choice + "님 인증되었습니다.")
                        display_time = time.time()
                        information_time = time.time()
                        # choice 님 인증되었습니다.
                        # 온도가 높습니다.
                        # 등등 information Message 출력
                        time.sleep(2)
                        while captureFrame.qsize() != 0:
                            captureFrame.get()
                        while analizeResult.qsize() != 0:
                            analizeResult.get()
                    delay_time = time.time()

                app.change_img(frame)

    def terminate(self):
        self.flag = False
        logShow("ThreadRecognition Thread terminate")


def ImageAnalize(i, shareResource, captureFrame, analizeResult):
    logShow(str(i) + " process enter")
    # 1 = run, 2 = sleep
    flag = 2
    while shareResource["imageAnalizeFlag"] > 0:
        if shareResource["imageAnalizeFlag"] == 1:
            flag = 1
        elif shareResource["imageAnalizeFlag"] == 2:
            flag = 2
        elif shareResource["imageAnalizeFlag"] == 3:
            _, _, col, error_col, names, id = mill_faceDB().access_db()
            flag = 2
        elif shareResource["imageAnalizeFlag"] == 4:
            _, _, col, error_col, names, id = mill_faceDB().access_db()
            flag = 1
        if flag == 2:
            logShow(str(i) + " process(ImageAnalize) sleep")
            time.sleep(0.2)
            continue
        # try:
        logShow(str(i) + " process(ImageAnalize) face_locations start captureFrame size = " + str(captureFrame.qsize()))
        frame = captureFrame.get()
        face_locations = fr.face_locations(frame)
        logShow(str(i) + " process(ImageAnalize) face_locations end")
        if len(face_locations) == 1:
            f1 = np.copy(frame)
            # rectangle
            face_crop = face_locations[0]
            cv2.rectangle(f1,
                          (face_crop[3], face_crop[0]),
                          (face_crop[1], face_crop[2]),
                          (0, 0, 255), 2)
            logShow(str(i) + " process(ImageAnalize) face_encodings start")
            face_encodings = fr.face_encodings(frame, face_locations)
            logShow(str(i) + " process(ImageAnalize) face_encodings end")
            name = defaultName
            for fe in face_encodings:
                face_distances = fr.face_distance(id, fe)
                best_match_index = np.argmin(face_distances)
                if face_distances[best_match_index] < setting["distance"]:
                    name = names[best_match_index]
                    analizeResult.put(name)
            logShow(str(i) + "DB search end, search name :" + name)
        # except:
        #     pass

    logShow(str(i) + " process(ImageAnalize) end")


def logShow(string):
    if log:
        lg = open(datetime.now().strftime("%Y%m%d_") + setting["log"] + ".txt", "a")
        lg.write(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " :::: {}\n".format(string))
        lg.close()
    if debug:
        print(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " :::: ", end="")
        print(string)


# ------------------------------------------------------------------------------------------------------------------
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

# 디버그 출력 유무
try:
    debug = setting["debug"]
    debug = True
except:
    debug = False

# 카메라 전역변수
cam = cv2.VideoCapture(cam_num, cam_cap)
camFlag = False
cap_size = (setting["camera"]["roi"]["width"], setting["camera"]["roi"]["height"])
captureFrame = multiprocessing.Queue()
analizeResult = multiprocessing.Queue()
pro_list = []
defaultName = "- - -"
app = layout_controller()


def programExit():
    app.programExit()
    app.destroy()


if __name__ == "__main__":
    logShow("start main")
    logShow("cpu_count : " + str(core_count))
    logShow("camera connected : " + str(cam.isOpened()))

    shareResource = multiprocessing.Manager().dict()
    # imageAnalizeFlag
    # 0 = terminate, 1 = run, 2 = sleep, 3 = db sync > sleep, 4 = db sync > run
    shareResource["imageAnalizeFlag"] = 3

    for i in range(core_count):
        logShow(str(i) + " process start")
        p = Process(target=ImageAnalize, args=(i, shareResource, captureFrame, analizeResult))
        pro_list.append(p)
        p.start()

    # app.attributes("-fullscreen", True)
    app.bind("<F11>", lambda event: app.attributes(
        "-fullscreen", not app.attributes("-fullscreen")))
    app.protocol("WM_DELETE_WINDOW", programExit)
    app.mainloop()

    for process in pro_list:
        process.kill()

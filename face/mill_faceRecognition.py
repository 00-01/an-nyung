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
from PIL import Image, ImageFont, ImageDraw
from PIL import ImageTk

from mill_faceDB import mill_faceDB


class layout_controller(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self._layout = None
        self.switch_layout(layout_start)

    # layout switch용
    def switch_layout(self, new_layout):
        new_frame = new_layout(self)
        if self._layout is not None:
            self._layout.destroy()
        self._layout = new_frame
        self._layout.pack(fill="both", expand=True)

    def programExit(self):
        if self._layout is not None:
            self._layout.programExit()

        cam.release()


class layout_start(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master

        if setting_viewType == 1:
            tk.Button(self, text="Go to layout_faceCapture",
                      command=lambda: self.go_faceCapture()).pack(side="bottom", fill="both")
            tk.Button(self, text="Go to layout_faceRecognition",
                      command=lambda: self.go_faceRecognition()).pack(side="bottom", fill="both")
            img = Image.open("layout/background.jpg")
            if setting_fullscreen:
                img = img.resize((master.winfo_screenwidth(), master.winfo_screenheight()), Image.LANCZOS)
            self.img = ImageTk.PhotoImage(img)
            tk.Label(self, image=self.img).pack(side="top")

        elif setting_viewType == 2:
            self.background = tk.Label(self)
            self.background.pack(fill="both", expand=True)

            img = cv2.imread("layout/background.jpg")
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if setting_fullscreen:
                img = cv2.resize(img, (master.winfo_screenwidth(), master.winfo_screenheight()))
            font = ImageFont.truetype(setting_fontPath, 20)
            img_pil = Image.fromarray(img)
            draw = ImageDraw.Draw(img_pil)
            draw.text((150, 500), "아래 해당되는 숫자를 입력해주세요. 1, 2, 3", font=font, fill=(255, 255, 255, 0))
            draw.text((150, 550), "1. 신규 사용자 등록", font=font, fill=(255, 255, 255, 0))
            draw.text((150, 600), "2. 얼굴인식", font=font, fill=(255, 255, 255, 0))
            draw.text((150, 650), "3. 종료(ESC)", font=font, fill=(255, 255, 255, 0))
            img = np.array(img_pil)
            img = Image.fromarray(img)

            self.src = ImageTk.PhotoImage(image=img)
            self.background.config(image=self.src)
            self.background.image = self.src

            self.master.bind("1", lambda x: self.go_faceCapture())
            self.master.bind("2", lambda x: self.go_faceRecognition())
            self.master.bind("3", lambda x: programExit())
            self.master.bind("<Escape>", lambda x: programExit())

    def go_faceCapture(self):
        self.master.unbind("1")
        self.master.unbind("2")
        self.master.unbind("3")
        self.master.unbind("<Escape>")
        self.master.switch_layout(layout_faceCapture)

    def go_faceRecognition(self):
        self.master.unbind("1")
        self.master.unbind("2")
        self.master.unbind("3")
        self.master.unbind("<Escape>")
        self.master.switch_layout(layout_faceRecognition)

    def programExit(self):
        pass


class layout_faceCapture(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master

        if setting_viewType == 1:
            self.frame = tk.Frame(self)
            self.frame.pack(side="bottom", fill="both")

            tk.Button(self.frame, text="Save",
                      command=self.save_face).pack(side="left")
            self.name = tk.Entry(self.frame)
            self.name.pack(side="left", fill="both", expand=True)

            tk.Button(self.frame, text="Back",
                      command=self.go_back).pack(side="right")


        elif setting_viewType == 2:
            self.name = tk.Entry(self)
            self.name.pack(side="bottom", fill="both", expand=True)

            self.name.bind("<Return>", lambda x: self.save_face())
            self.name.bind("<Escape>", lambda x: self.go_back())

        # 출력할 이미지 위젯
        self.camera = tk.Label(self)
        self.camera.pack(side="top")

        self.information = tk.Label(self)

        # self.information = tk.Label(self, fg="#f00", text="안녕", font=("H2GTRM", 30))

        self.name.focus_set()
        # self.information.place(x=0, y=100, width=master.winfo_screenwidth(), height=40)

        # 촬영 thread 시작
        self.ThreadCapture = ThreadCapture()
        threading.Thread(target=self.ThreadCapture.run, args=(self,)).start()

    def save_face(self):
        # 이름 설정 안했을 경우 취소
        if len(self.name.get()) == 0:
            return

        # 이미지가져옴>쓰레드 종료>다이얼로그>확인,취소>쓰레드재시작
        ret, frame = cam.read()

        if ret:
            # 쓰레드 종료
            self.ThreadCapture.terminate()
            face_crop = fr.face_locations(frame)

            # 얼굴 인식 못할경우 촬영으로 재시작
            if len(face_crop) == 0:
                self.imformation_show("인식된 얼굴이 없습니다.", 1)
                logShow("no search face location")
                self.ThreadCapture = ThreadCapture()
                self.ThreadCapture.information_time = time.time()
                threading.Thread(target=self.ThreadCapture.run, args=(self,)).start()
                return
            elif len(face_crop) > 1:
                self.imformation_show("얼굴이 2명 이상 검색되었습니다.", 1)
                # self.information.config(text="얼굴이 2명 이상 검색되었습니다.")
                logShow("more 2 search face location")
                self.ThreadCapture = ThreadCapture()
                self.ThreadCapture.information_time = time.time()
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

            if setting_viewType == 2:
                self.name.unbind("<Return>")
                self.name.unbind("<Escape>")
                # dialog에 필요한 key bind

            # 저장하시겠습니까 메세지 다이얼로그
            btn = dialog_saveFace(self, self.name.get(), tmp1).show()
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
                    self.imformation_show("신규사용자 " + name + " 저장되었습니다.", 2)

                except IndexError:
                    error_col.insert_one({'name': name})
                    # os.remove(captured_img)
                    self.imformation_show('warning! face not detected! : ' + name, 1)
                    logShow("save new db error" + name)

            # 촬영 쓰레드 재시작
            self.ThreadCapture = ThreadCapture()
            threading.Thread(target=self.ThreadCapture.run, args=(self,)).start()

            if setting_viewType == 2:
                self.name.bind("<Return>", lambda x: self.save_face())
                self.name.bind("<Escape>", lambda x: self.go_back())

    def change_img(self, img):  # 레이블의 이미지 변경
        try:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if setting_fullscreen:
                img = cv2.resize(img, (self.master.winfo_screenwidth(), self.master.winfo_screenheight()))
            img = Image.fromarray(img)
            self.src = ImageTk.PhotoImage(image=img)
            self.camera.config(image=self.src)
            self.camera.image = self.src
        except:
            pass

    def imformation_show(self, msg, flag):
        # flag
        # 0 : normal
        # 1 : err   /back = yellow, fontcolor = red
        # 2 : success
        font = ImageFont.truetype(setting_fontPath, 20)
        if flag == 0:
            pass

        elif flag == 1:
            img = np.full((50, self.master.winfo_screenwidth(), 3), (255, 0, 0), np.uint8)
            img_pil = Image.fromarray(img)
            draw = ImageDraw.Draw(img_pil)
            draw.text((0, 10), msg, font=font, fill=(255, 255, 255, 0))
        elif flag == 2:
            img = np.full((50, self.master.winfo_screenwidth(), 3), (0, 255, 0), np.uint8)
            img_pil = Image.fromarray(img)
            draw = ImageDraw.Draw(img_pil)
            draw.text((0, 10), msg, font=font, fill=(0, 0, 0, 0))

        img = np.array(img_pil)
        img = Image.fromarray(img)

        self.informationSrc = ImageTk.PhotoImage(image=img)
        self.information.config(image=self.informationSrc)
        self.information.image = self.informationSrc

        self.information.place(x=0, y=100, width=self.master.winfo_screenwidth(), height=40)
        self.ThreadCapture.informationFlag = True

    def go_back(self):
        self.name.unbind("<Return>")
        self.name.unbind("<Escape>")
        self.ThreadCapture.terminate()
        self.master.switch_layout(layout_start)

    def programExit(self):
        self.ThreadCapture.terminate()


class dialog_saveFace(tk.Toplevel):
    def __init__(self, parent, name, img):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        # 저장하시겠습니까?
        self.click = False  # OK : True, NO : False

        if setting_viewType == 1:
            btn_cancel = tk.Button(self, text="NO", command=self.click_cancel)
            btn_cancel.pack(side="right")
            btn_ok = tk.Button(self, text="OK", command=self.click_ok)
            btn_ok.pack(side="right")
            tk.Label(self, text=name + "으로 저장하시겠습니까?").pack(side="right", fill="x")
        elif setting_viewType == 2:
            tk.Label(self, text=name + "으로 저장하시겠습니까?").pack(side="bottom", fill="x")
            parent.name.bind("<Return>", lambda x: self.click_ok())
            parent.name.bind("<Escape>", lambda x: self.click_cancel())

        self.capture = tk.Label(self)
        img = cv2.flip(img, 1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        self.src = ImageTk.PhotoImage(image=img)
        self.capture.config(image=self.src)
        self.capture.image = self.src
        self.capture.pack(side="top")

    def click_ok(self):
        if setting_viewType == 2:
            self.parent.name.unbind("<Return>")
            self.parent.name.unbind("<Escape>")
        self.click = True
        self.destroy()

    def click_cancel(self):
        if setting_viewType == 2:
            self.parent.name.unbind("<Return>")
            self.parent.name.unbind("<Escape>")
        self.destroy()

    def show(self):
        self.wm_deiconify()
        self.wait_window()
        return self.click


class ThreadCapture():
    def __init__(self):
        self.flag = True
        self.information_time = time.time()
        self.informationFlag = False

    def run(self, layout):
        self.flag = True
        while self.flag:
            if self.informationFlag:
                if time.time() - self.information_time > setting_information_time:
                    layout.information.place_forget()
                    self.informationFlag = False
            ret, frame = cam.read()
            if ret:
                img = cv2.flip(frame, 1)
                layout.change_img(img)
            cv2.waitKey(10)

    def terminate(self):
        self.flag = False
        logShow("ThreadCapture Thread terminate")


class layout_faceRecognition(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master
        self.src = None

        # 출력할 이미지 위젯
        self.camera = tk.Label(self)
        self.camera.pack(side="top")

        self.frame = tk.Frame(self)
        self.frame.pack(side="bottom")

        tk.Button(self.frame, text="Back",
                  command=self.go_back).pack(side="right")

        self.information = tk.Label(self)

        # 촬영 thread 시작
        self.ThreadRecognition = ThreadRecognition()
        threading.Thread(target=self.ThreadRecognition.run, args=(self,)).start()

    def change_img(self, img):  # 레이블의 이미지 변경
        try:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if setting_fullscreen:
                img = cv2.resize(img, (self.master.winfo_screenwidth(), self.master.winfo_screenheight()))
            img = Image.fromarray(img)
            self.src = ImageTk.PhotoImage(image=img)
            self.camera.config(image=self.src)
            self.camera.image = self.src
        except:
            pass

    def imformation_show(self, msg, flag):
        # flag
        # 0 : normal
        # 1 : err   /back = yellow, fontcolor = red
        # 2 : success
        font = ImageFont.truetype(setting_fontPath, 20)
        if flag == 0:
            pass

        elif flag == 1:
            img = np.full((50, self.master.winfo_screenwidth(), 3), (255, 0, 0), np.uint8)
            img_pil = Image.fromarray(img)
            draw = ImageDraw.Draw(img_pil)
            draw.text((0, 10), msg, font=font, fill=(255, 255, 255, 0))
        elif flag == 2:
            img = np.full((50, self.master.winfo_screenwidth(), 3), (0, 255, 0), np.uint8)
            img_pil = Image.fromarray(img)
            draw = ImageDraw.Draw(img_pil)
            draw.text((0, 10), msg, font=font, fill=(0, 0, 0, 0))

        img = np.array(img_pil)
        img = Image.fromarray(img)

        self.informationSrc = ImageTk.PhotoImage(image=img)
        self.information.config(image=self.informationSrc)
        self.information.image = self.informationSrc

        self.information.place(x=0, y=100, width=self.master.winfo_screenwidth(), height=40)
        self.ThreadRecognition.informationFlag = True

    def go_back(self):
        shareResource["imageAnalizeFlag"] = 2
        self.ThreadRecognition.terminate()
        self.master.switch_layout(layout_start)

    def programExit(self):
        shareResource["imageAnalizeFlag"] = 0
        self.ThreadRecognition.terminate()


class ThreadRecognition():
    def __init__(self):
        self.flag = True
        self.informationFlag = False

    def run(self, layout):
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
            if self.informationFlag:
                if time.time() - information_time > setting_information_time:
                    layout.information.place_forget()
                    self.informationFlag = False
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

                if time.time() - display_time > setting_displayout_time and motionFlag:
                    logShow("displayout")
                    motionFlag = False
                    shareResource["imageAnalizeFlag"] = 2

                    canvas = np.copy(frame)
                    canvas[:] = 0
                    fontpath = "fonts/gulim.ttc"
                    font = ImageFont.truetype(fontpath, 20)
                    img_pil = Image.fromarray(canvas)
                    draw = ImageDraw.Draw(img_pil)
                    draw.text((60, 70), "잠시 쉬고있습니다. 움직여서 깨워주세요.", font=font, fill=(255, 255, 255, 0))
                    img = np.array(img_pil)
                    layout.change_img(img)

                if not motionFlag:
                    continue

                # ---------------------------------------조도 파악해서 light

                frame = cv2.flip(frame, 1)
                # cpu 코어 갯수 - 2개 만큼만 face_recognition돌림
                # video capture돌아가는 1개
                # UI cs 1개
                if captureFrame.qsize() < setting_core_count and time.time() - start_time > float(
                        1) / setting_core_count:
                    start_time = time.time()
                    # ROI
                    # 중앙에서 cap_size만큼
                    captureFrame.put(
                        frame[int(frame.shape[0] / 2 - setting_cap_size[1] / 2): int(
                            frame.shape[0] / 2 + setting_cap_size[1] / 2),
                        int(frame.shape[1] / 2 - setting_cap_size[0] / 2): int(
                            frame.shape[1] / 2 + setting_cap_size[0] / 2)])
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
                if setting_view_roi:
                    cv2.imshow('roi',
                               frame[
                               int(frame.shape[1] / 2 - setting_cap_size[0] / 2): int(
                                   frame.shape[0] / 2 + setting_cap_size[1] / 2),
                               int(frame.shape[1] / 2 - setting_cap_size[0] / 2): int(
                                   frame.shape[0] / 2 + setting_cap_size[1] / 2)])

                # ROI사각형
                cv2.rectangle(frame,
                              (int(frame.shape[1] / 2 - setting_cap_size[0] / 2),
                               int(frame.shape[0] / 2 - setting_cap_size[1] / 2)),
                              (int(frame.shape[1] / 2 + setting_cap_size[0] / 2),
                               int(frame.shape[0] / 2 + setting_cap_size[1] / 2)),
                              (0, 0, 255), 2)
                # fps출력
                if setting_view_fps:
                    cv2.putText(frame, "fps : " + str(fps), (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1,
                                cv2.LINE_AA)

                cv2.waitKey(10)
                certification = False
                if time.time() - delay_time > setting_collect_time:
                    if analizeResult.qsize() != 0:
                        ls = []
                        for _ in range(analizeResult.qsize()):
                            ls.append(analizeResult.get())
                        choice = max(ls, key=ls.count)
                        logShow("search list : " + " ".join(ls))
                        logShow("detect name : " + choice)
                        if not setting_debug:
                            print(datetime.now().strftime("%H:%M:%S") + " list : " + " ".join(ls))
                            print(datetime.now().strftime("%H:%M:%S") + " name : " + choice)
                        certification = True

                        # get RFID MODULE
                        layout.imformation_show(choice + "님 인증되었습니다.", 2)
                        # layout.imformation_show("카드가 일치하지 않습니다.", 1)
                        display_time = time.time()
                        information_time = time.time()
                        # choice 님 인증되었습니다.
                        # 온도가 높습니다.
                        # 등등 information Message 출력
                        time.sleep(setting_sign_time)
                        while captureFrame.qsize() != 0:
                            captureFrame.get()
                        while analizeResult.qsize() != 0:
                            analizeResult.get()
                    delay_time = time.time()

                layout.change_img(frame)

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
                if face_distances[best_match_index] < setting["threshold"]:
                    name = names[best_match_index]
                    analizeResult.put(name)
            logShow(str(i) + " process(DB) search end, search name :" + name)
        # except:
        #     pass

    logShow(str(i) + " process(ImageAnalize) end")


def logShow(string):
    if setting_log:
        lg = open(datetime.now().strftime("%Y%m%d_") + "log.txt", "a")
        lg.write(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " :::: {}\n".format(string))
        lg.close()

    if setting_debug:
        print(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " :::: ", end="")
        print(string)


# -----------------------------------------------------setting-------------------------------------------------------------
with open('config.json') as json_file:
    setting = json.load(json_file)

for s_os in setting["camera"]["os"]:
    if s_os in platform.platform():
        setting_cam_num = setting["camera"]["os"][s_os]["dev"]
        setting_cam_cap = setting["camera"]["os"][s_os]["cap"]
        break

# multiProcess에 쓸 코어 갯수
try:
    setting_core_count = setting["core"]
    if setting_core_count > multiprocessing.cpu_count() - 2:
        setting_core_count = multiprocessing.cpu_count() - 2
except:
    setting_core_count = multiprocessing.cpu_count() - 2

# 로그작업 유무
try:
    setting_log = setting["log"]
    setting_log = True
except:
    setting_log = False

# 디버그 출력 유무
try:
    setting_debug = setting["debug"]
    setting_debug = True
except:
    setting_debug = False

setting_fontPath = setting["fontpath"]
setting_fullscreen = setting["fullscreen"]
setting_cap_size = (setting["camera"]["roi"]["width"], setting["camera"]["roi"]["height"])
setting_view_fps = setting["view"]["fps"]
setting_view_roi = setting["view"]["roi"]
setting_collect_time = setting["collectTime"]
setting_displayout_time = setting["displayoutTime"]
setting_information_time = setting["informationTime"]
setting_sign_time = setting["signTime"]
setting_viewType = setting["viewType"]
# -----------------------------------------------------setting-------------------------------------------------------------


cam = cv2.VideoCapture(setting_cam_num, setting_cam_cap)
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
    logShow("cpu_count : " + str(setting_core_count))
    logShow("camera connected : " + str(cam.isOpened()))

    shareResource = multiprocessing.Manager().dict()
    # imageAnalizeFlag
    # 0 = terminate, 1 = run, 2 = sleep, 3 = db sync > sleep, 4 = db sync > run
    shareResource["imageAnalizeFlag"] = 3

    for i in range(setting_core_count):
        logShow(str(i) + " process start")
        p = Process(target=ImageAnalize, args=(i, shareResource, captureFrame, analizeResult))
        pro_list.append(p)
        p.start()

    if setting_fullscreen:
        app.attributes("-fullscreen", True)
        app.bind("<F11>", lambda event: app.attributes(
            "-fullscreen", not app.attributes("-fullscreen")))
    app.protocol("WM_DELETE_WINDOW", programExit)
    app.mainloop()

    for process in pro_list:
        process.kill()

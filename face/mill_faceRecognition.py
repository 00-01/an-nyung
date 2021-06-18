import datetime
import json
import os
import platform
import threading
import cv2
import tkinter as tk
import numpy as np
import qimage2ndarray
from PIL import ImageTk
from PIL import Image
import face_recognition as fr
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
                  command=lambda: master.switch_frame(layout_faceRecognition)).pack(side="bottom", expand=True, fill="both")

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

        #이름 설정 안했을 경우 취소
        if len(self.name.get()) == 0:
            return

        #이미지가져옴>쓰레드 종료>메세지박스>확인,취소>쓰레드재시작
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
        
        #얼굴 인식됨
        face_crop = face_crop[0]
        tmp1 = np.copy(frame)
        cv2.rectangle(tmp1,
                      (face_crop[3], face_crop[0]),
                      (face_crop[1], face_crop[2]),
                      (0, 0, 255), 2)
        
        #저장하시겠습니까 메세지 다이얼로그
        btn = SaveCaptureDialog(self, self.name.get() + "으로 저장하시겠습니까?", tmp1).show()
        if btn:
            name = self.name.get()
            captured_img = "tmp/" + name + "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
            #인식된 이미지(얼굴만)
            frame = frame[face_crop[0]:face_crop[2], face_crop[3]:face_crop[1]]
            if not os.path.isdir("tmp"):
                os.mkdir("tmp")
            cv2.imwrite(captured_img, frame)
            
            #DB에 넣음
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
        
        #촬영 쓰레드 재시작
        self.ThreadCapture = ThreadCapture()
        threading.Thread(target=self.ThreadCapture.run, args=(self,)).start()

        #name widget text 리셋
        self.name.delete(0, 'end')


    def click_back(self):
        self.ThreadCapture.terminate()
        self.master.switch_frame(layout_start)

    def change_img(self, img):  # 레이블의 이미지 변경
        try:
            img = cv2.flip(img, 1)
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
        #저장하시겠습니까?
        self.click = False # OK : True, NO : False

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
                app.change_img(frame)
            cv2.waitKey(100)

    def terminate(self):
        self.flag = False

#아직 이식안함
class layout_faceRecognition(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Frame.configure(self,bg='blue')
        tk.Label(self, text="Page one", font=('Helvetica', 18, "bold")).pack(side="top", fill="x", pady=5)
        tk.Button(self, text="Go back to start page",
                  command=lambda: master.switch_frame(layout_start)).pack()




with open('config.json') as json_file:
    setting = json.load(json_file)

for s_os in setting["camera"]["os"]:
    if s_os in platform.platform():
        cam_num = setting["camera"]["os"][s_os]["dev"]
        cam_cap = setting["camera"]["os"][s_os]["cap"]
        break

cam = cv2.VideoCapture(cam_num, cam_cap)
#카메라 전역변수

if __name__ == "__main__":
    app = layout_controller()
    app.mainloop()



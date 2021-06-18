import threading

import cv2
import tkinter as tk
from PIL import ImageTk
from PIL import Image

# def convert_to_tkimage():
#     global src
#
#     gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
#     _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
#
#     img = Image.fromarray(binary)
#     imgtk = ImageTk.PhotoImage(image=img)
#
#     label.config(image=imgtk)
#     label.image = imgtk




class layout_controller(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self._frame = None
        self.switch_frame(layout_start)

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
        self.flag = False
        self.flag = True
        #camera
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
        self.captureThread = threading.Thread(target=preview_th, args=(lambda:self.flag, self))
        self.captureThread.daemon = True
        self.captureThread.start()


    def click_save(self):
        #이미지가져옴>쓰레드 종료>메세지박스>확인,취소>쓰레드재시작
        self.camera
        self.flag = False
        



    def click_back(self):
        self.flag = False
        self.master.switch_frame(layout_start)

    def change_img(self, img):  # 레이블의 이미지 변경
        try:
            img = cv2.flip(img, 1)
            img = cv2.resize(img, (640, 400))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            self.src = ImageTk.PhotoImage(image=img)
            self.camera['image'] = self.src
        except:
            pass

def preview_th(stop, app):
    while stop:
        ret, frame = cam.read()
        if ret:
            app.change_img(frame)
        cv2.waitKey(100)


class layout_faceRecognition(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Frame.configure(self,bg='blue')
        tk.Label(self, text="Page one", font=('Helvetica', 18, "bold")).pack(side="top", fill="x", pady=5)
        tk.Button(self, text="Go back to start page",
                  command=lambda: master.switch_frame(layout_start)).pack()








cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)


if __name__ == "__main__":
    app = layout_controller()
    app.mainloop()



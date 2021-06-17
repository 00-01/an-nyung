


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


        self.imgtk = ImageTk.PhotoImage(file="layout/background.png")

        tk.Label(self, image=self.imgtk).pack(side="top")



        #tk.Label(self, text="Start page", font=('Helvetica', 18, "bold")).pack(side="top", fill="x", pady=5)
        tk.Button(self, text="Go to page layout_faceCapture",
                  command=lambda: master.switch_frame(layout_faceCapture)).pack()
        tk.Button(self, text="Go to page layout_faceRecognition",
                  command=lambda: master.switch_frame(layout_faceRecognition)).pack()


class layout_faceRecognition(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Frame.configure(self,bg='blue')
        tk.Label(self, text="Page one", font=('Helvetica', 18, "bold")).pack(side="top", fill="x", pady=5)
        tk.Button(self, text="Go back to start page",
                  command=lambda: master.switch_frame(layout_start)).pack()

class layout_faceCapture(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Frame.configure(self,bg='red')
        tk.Label(self, text="Page two", font=('Helvetica', 18, "bold")).pack(side="top", fill="x", pady=5)
        tk.Button(self, text="Go back to start page",
                  command=lambda: master.switch_frame(layout_start)).pack()









if __name__ == "__main__":
    app = layout_controller()
    app.mainloop()



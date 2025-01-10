import tkinter as tk
from PIL import ImageGrab
from PIL import Image, ImageTk
from io import BytesIO
import pytesseract
import numpy as np
import cv2
from collections import defaultdict

pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

def ocr_box(image):
    text_data = pytesseract.image_to_data(image, lang='eng')
    data = defaultdict(list)

    for i, line in enumerate(text_data.splitlines()):
       
        if i == 0:
            continue  
        line = line.split()
        block_num = line[2] * 1000000 + line[3]*1000 + line[4]
        if len(line) == 12: 
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9]) 
            
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 1)
            data[block_num].append(line[-1])

    return image, [" ".join(data[k])for k in data.keys() ]

class TranslateApp:
    def __init__(self, root):
        self.root = root
        self.setup_frame_A()
        self.setup_frame_B()
        self.update_capture()

    def setup_frame_A(self):
        self.frame_A = tk.Toplevel(self.root)
        self.frame_A.title('캡쳐')
        self.frame_A.geometry('300x200') 
        self.frame_A.wm_attributes('-transparentcolor', self.frame_A['bg']) 
        
    def setup_frame_B(self):
        self.frame_B = tk.Toplevel(self.root)
        self.frame_B.geometry('300x600+400+100')
        self.frame_B.title('메인')

        self.label = tk.Label(self.frame_B) # 캡쳐한 이미지를 보여줄 예정이라 빈칸
        self.label.pack(fill=tk.BOTH, expand=True)

        # OCR 인식 텍스트를 보여줄 레이블
        self.ocr_text_label = tk.Label(self.frame_B, text="OCR 인식 텍스트", bg="white", height=10)
        self.ocr_text_label.pack(fill=tk.X, expand=True)


        # 번역된 텍스트를 보여줄 레이블
        self.trans_text_label = tk.Label(self.frame_B, text="번역 텍스트", bg="white", height=10)
        self.trans_text_label.pack(fill=tk.X, expand=True)

    def set_text(self, text):
        self.ocr_text_label.config(text=text)

    def set_trans_text(self, text):
        self.trans_text_label.config(text=text)

    def update_capture(self):
        title_bar_height = 31  
        border_width = 8

        x = self.frame_A.winfo_x()
        y = self.frame_A.winfo_y()
        width = self.frame_A.winfo_width()
        height = self.frame_A.winfo_height()

        image = ImageGrab.grab(bbox=(x+border_width, y+title_bar_height, x + border_width+ width, y + title_bar_height + height),all_screens=True)

        if image == None:
            self.label.config(image=None)
            return

        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        photo = tk.PhotoImage(data=img_byte_arr.read())

        self.label.config(image=photo)
        self.label.image = photo

        self.frame_A.after(1000, self.update_capture)

root = tk.Tk()
root.withdraw() # 프레임만 띄울거라 메인 루트는 가린다.
app = TranslateApp(root)

# Run the app
root.mainloop()
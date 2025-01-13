import tkinter as tk
import pytesseract
import numpy as np
import cv2
from PIL import ImageGrab, Image, ImageTk
from io import BytesIO
from collections import defaultdict

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def ocr_box(image):
    # PIL 이미지를 NumPy 배열로 변환
    image_cv = np.array(image)
    
    # PIL 이미지가 BGR 형식으로 변환되므로 RGB로 변경
    if image_cv.shape[-1] == 4:  # RGBA에서 RGB로 변환
        image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGBA2RGB)
    elif image_cv.shape[-1] == 3:  # RGB 형식일 경우 그대로 사용
        pass
    else:
        raise ValueError("지원되지 않는 이미지 형식")

    text_data = pytesseract.image_to_data(image_cv, lang='eng')
    data = defaultdict(list)

    for i, line in enumerate(text_data.splitlines()):
        if i == 0:
            # 첫 번째 줄은 헤더 정보이므로 건너뜀
            continue
        
        line = line.split()
        if len(line) < 12:
            # 데이터가 불완전한 경우 건너뜀
            continue
        
        try:
            # 블록 ID 생성
            block_num = int(line[2]) * 1000000 + int(line[3]) * 1000 + int(line[4])
            x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
            cv2.rectangle(image_cv, (x, y), (x + w, y + h), (0, 255, 0), 1)
            data[block_num].append(line[-1])
        except ValueError:
            # 예상치 못한 데이터 형식이 있는 경우 건너뜀
            continue

    # OCR 결과 반환
    text_results = [" ".join(data[k]) for k in sorted(data.keys())]
    
    # 다시 NumPy 배열을 PIL 이미지로 변환
    image_pil = Image.fromarray(image_cv)
    return image_pil, text_results

class TranslateApp:
    def __init__(self, root):
        self.root = root
        self.setup_frame_A()
        self.setup_frame_B()
        self.update_capture()

    def setup_frame_A(self):
        self.frame_A = tk.Toplevel(self.root)
        self.frame_A.title('캡쳐')
        self.frame_A.geometry('300x200')  # 창 크기 설정
        self.frame_A.wm_attributes('-transparentcolor', self.frame_A['bg'])  # 배경 투명 설정

    def setup_frame_B(self):
        self.frame_B = tk.Toplevel(self.root)
        self.frame_B.geometry('300x600+400+100')
        self.frame_B.title('메인')

        self.label = tk.Label(self.frame_B)  # 캡처한 이미지를 보여줄 레이블
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
        try:
            # 윈도우 창의 실제 화면 좌표 계산
            x1 = self.frame_A.winfo_rootx()
            y1 = self.frame_A.winfo_rooty()
            x2 = x1 + self.frame_A.winfo_width()
            y2 = y1 + self.frame_A.winfo_height()

            # 캡처 수행
            image = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)

            # OCR 처리
            processed_image, text_results = ocr_box(image)

            # OCR 결과 텍스트를 메인 창에 표시
            self.set_text("\n".join(text_results))

            # PIL 이미지를 ImageTk로 변환
            photo = ImageTk.PhotoImage(processed_image)

            # 캡처된 이미지를 레이블에 표시
            self.label.config(image=photo)
            self.label.image = photo

        except Exception as e:
            print(f"캡처 중 오류 발생: {e}")

        # 빠르게 캡처 업데이트 (100ms 주기)
        self.frame_A.after(100, self.update_capture)


root = tk.Tk()
root.withdraw()  # 기본 창 숨김
app = TranslateApp(root)

root.mainloop()
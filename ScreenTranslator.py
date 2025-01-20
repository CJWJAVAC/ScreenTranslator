import tkinter as tk
import pytesseract
import numpy as np
import cv2
from PIL import ImageGrab, Image, ImageTk
from io import BytesIO
from collections import defaultdict
import requests

url = "https://api-free.deepl.com/v2/translate"
headers = {
    "Authorization": "DeepL-Auth-Key 8e012d61-9bd1-4f2e-9dab-fb32a0bff1c4:fx"
}

def translate(text):
    data = {
        "text": text,
        "source_lang": "EN",
        "target_lang": "KO"
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        translated_json = response.json()
        return translated_json['translations'][0]['text']
    else:
        raise Exception(f"DeepL API 호출 실패: {response.status_code}, {response.text}")

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
        self.last_text = ""
        self.resizing = False
        self.start_x=0
        self.start_y=0
        self.translation_interval = 3000
        self.last_translation_time = 0

    def setup_frame_A(self):
        self.frame_A = tk.Toplevel(self.root)
        self.frame_A.title('캡쳐')
        self.frame_A.geometry('300x200')  # 창 크기 설정
        self.frame_A.wm_attributes('-transparentcolor', self.frame_A['bg'])  # 배경 투명 설정

        self.frame_A.bind("<ButtonPress-1>", self.start_resize)  # 왼쪽 클릭 시작
        self.frame_A.bind("<B1-Motion>", self.resize_frame)     # 드래그 중
        self.frame_A.bind("<ButtonRelease-1>", self.stop_resize)

    def setup_frame_B(self):
        self.frame_B = tk.Toplevel(self.root)
        self.frame_B.geometry('300x600+400+100')
        self.frame_B.title('메인')

        self.label = tk.Label(self.frame_B)  # 캡처한 이미지를 보여줄 레이블
        self.label.pack(fill=tk.BOTH, expand=True)

        # OCR 인식 텍스트를 보여줄 레이블
        self.ocr_text_label = tk.Label(self.frame_B, text="OCR 인식 텍스트", bg="white", height=10)
        self.ocr_text_label.pack(fill=tk.X, padx=10, pady=10)

        # 번역된 텍스트를 보여줄 레이블
        self.trans_text_label = tk.Label(self.frame_B, text="번역 텍스트", bg="white", height=10)
        self.trans_text_label.pack(fill=tk.X, padx=10, pady=10)

        self.frame_B.bind("<Configure>", self.update_wraplength)

    def update_wraplength(self, event):
        new_wraplength = event.width - 20
        self.ocr_text_label.config(wraplength=new_wraplength)
        self.trans_text_label.config(wraplength=new_wraplength)

    def start_resize(self, event):
        """크기 조정을 시작."""
        self.resizing = True
        self.start_x = event.x_root
        self.start_y = event.y_root

    def resize_frame(self, event):
        """드래그 중 프레임 크기를 조정."""
        if self.resizing:
            # 마우스 이동 거리 계산
            dx = event.x_root - self.start_x
            dy = event.y_root - self.start_y

            # 현재 창 크기 가져오기
            current_width = self.frame_A.winfo_width()
            current_height = self.frame_A.winfo_height()

            # 창 크기 업데이트
            new_width = max(100, current_width + dx)  # 최소 너비 제한
            new_height = max(50, current_height + dy)  # 최소 높이 제한
            self.frame_A.geometry(f"{new_width}x{new_height}")

            # 시작점 업데이트
            self.start_x = event.x_root
            self.start_y = event.y_root

    def stop_resize(self, event):
        """크기 조정을 종료."""
        self.resizing = False

    def set_text(self, text_lines):
        combined_text = " ".join(text_lines).strip()
        combined_text = " ".join(combined_text.split())

        self.ocr_text_label.config(text=combined_text)

        current_time = self.frame_A.winfo_toplevel().tk.call('clock', 'clicks')
        if len(combined_text)>10 and combined_text!=self.last_text and current_time - self.last_translation_time>self.translation_interval:
            try:
                translated_text = translate(combined_text)
                self.set_trans_text(translated_text)
                self.last_text = combined_text
                self.last_translation_time = current_time
            except Exception as e:
                print(f"번역 실패: {e}")
                self.set_trans_text("번역 실패:다시 시도하세요")

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

            if text_results:
                self.set_text(text_results)

            # PIL 이미지를 ImageTk로 변환
            photo = ImageTk.PhotoImage(processed_image)

            # 캡처된 이미지를 레이블에 표시
            self.label.config(image=photo)
            self.label.image = photo

        except Exception as e:
            print(f"캡처 중 오류 발생: {e}")

        # 빠르게 캡처 업데이트 (100ms 주기)
        self.frame_A.after(1000, self.update_capture)


root = tk.Tk()
root.withdraw()  # 기본 창 숨김
app = TranslateApp(root)

root.mainloop()
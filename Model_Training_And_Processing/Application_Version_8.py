import sys
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageOps
import joblib
import time
import json
import concurrent.futures
import pandas as pd
import threading
import queue
from datetime import datetime

# --- FIX LỖI PILLOW 10.0+ ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
    PIL.Image.linear_gradient = PIL.Image.new
# ---------------------------------------

import cv2
import numpy as np
import torch
from ultralytics import YOLO
from paddleocr import PaddleOCR
import easyocr
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel 

from underthesea import word_tokenize

# ==============================================================================
# HÀM LƯU LOG
# ==============================================================================
def write_log(text):
    print(text)
    with open("log_app_v8.txt", "a", encoding="utf-8") as f:
        f.write(str(text) + "\n")

# ==============================================================================
# CẤU HÌNH ĐƯỜNG DẪN
# ==============================================================================
BASE_DIR = r"D:\LuanVan"
YOLO_MODEL_PATH = os.path.join(BASE_DIR, 'models','Best_Medium_640_50e_10p_auto_20260119_1637.pt')
MODEL_DIR = os.path.join(BASE_DIR, 'models')

# Dùng V3 cho biển hiệu
DET_PATH = os.path.join(MODEL_DIR, 'ch_PP-OCRv3_det_infer')
REC_PATH = os.path.join(MODEL_DIR, 'en_PP-OCRv4_rec_infer')
CLS_PATH = os.path.join(MODEL_DIR, 'ch_ppocr_mobile_v2.0_cls_infer')
VIETOCR_WEIGHT_PATH = os.path.join(MODEL_DIR, 'vietocr_v2_stage1_3103_0917.pth')
CLASSIFIER_PATH = os.path.join(BASE_DIR, "model_phanloai_danhmuc_v7", "Linear_SVC_model.pkl")
EASYOCR_MODEL_DIR = os.path.join(MODEL_DIR, 'easyocr')

# [MODEL LORA 2]
BASE_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
QWEN_ADAPTER_PATH = os.path.join(MODEL_DIR, 'qwen_0.5b_adapter_final_Step1_v6_hybrid')

# ==============================================================================
# CLASS ZOOMABLE CANVAS
# ==============================================================================

class ZoomableCanvas(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, bg="#333333", highlightthickness=0)
        self.hbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.vbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.cv_img = None
        self.pil_img = None
        self.tk_img = None
        self.zoom_scale = 1.0
        self.image_id = None

        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)

    def load_cv2_image(self, cv_img):
        self.cv_img = cv_img.copy()
        img_rgb = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2RGB)
        self.pil_img = Image.fromarray(img_rgb)
        
        self.update_idletasks()
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw > 10 and ch > 10:
            iw, ih = self.pil_img.size
            self.zoom_scale = min(cw/iw, ch/ih) * 0.95
        else:
            self.zoom_scale = 1.0
            
        self.show_image()

    def show_image(self):
        if self.pil_img is None: return
        w, h = int(self.pil_img.width * self.zoom_scale), int(self.pil_img.height * self.zoom_scale)
        if w < 10 or h < 10: return
        
        resized = self.pil_img.resize((w, h), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(resized)
        
        if self.image_id is not None:
            self.canvas.delete(self.image_id)
        
        self.image_id = self.canvas.create_image(max(self.canvas.winfo_width()//2, w//2), 
                                                 max(self.canvas.winfo_height()//2, h//2), 
                                                 anchor=tk.CENTER, image=self.tk_img)
        self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))

    def on_mousewheel(self, event):
        if self.pil_img is None: return
        scale_factor = 1.1 if event.delta > 0 else 0.9
        self.zoom_scale *= scale_factor
        self.zoom_scale = max(0.1, min(self.zoom_scale, 10.0))
        self.show_image()

    def on_button_press(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def on_move_press(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def clear(self):
        self.canvas.delete("all")
        self.cv_img = None; self.pil_img = None; self.tk_img = None


# ==============================================================================
# LÕI XỬ LÝ BACKEND 
# ==============================================================================
class OCRBackend:
    def __init__(self):
        print("Đang tải models YOLO, OCR...")
        self.yolo = YOLO(YOLO_MODEL_PATH)
        
        self.paddle = PaddleOCR(det_model_dir=DET_PATH, rec_model_dir=REC_PATH, cls_model_dir=CLS_PATH,
                                det_limit_side_len=1024, det_db_unclip_ratio=1.2, det_db_thresh=0.3,       
                                det_db_box_thresh=0.5, use_angle_cls=True, lang='en', show_log=False, rec=False, use_gpu=True)
        
        try:
            self.easyocr = easyocr.Reader(['vi', 'en'], gpu=True, model_storage_directory=EASYOCR_MODEL_DIR, download_enabled=False)
            print("Đã tải thành công EasyOCR (CRAFT)!")
        except Exception as e:
            print(f"LỖI TẢI EasyOCR: {e}")
            self.easyocr = None

        config = Cfg.load_config_from_name('vgg_transformer')
        config['weights'] = VIETOCR_WEIGHT_PATH
        config['cnn']['pretrained'] = False
        config['device'] = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.vietocr = Predictor(config)

        self.classifier = joblib.load(CLASSIFIER_PATH) if os.path.exists(CLASSIFIER_PATH) else None
        
        try:
            self.qwen_tokenizer = AutoTokenizer.from_pretrained(QWEN_ADAPTER_PATH) 
            has_gpu = torch.cuda.is_available()
            base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_ID, torch_dtype=torch.float16 if has_gpu else torch.float32,
                                                              device_map="auto" if has_gpu else None, offload_folder="offload_qwen")
            if not has_gpu: base_model = base_model.to("cpu")
            self.qwen_llm = PeftModel.from_pretrained(base_model, QWEN_ADAPTER_PATH)
            print("Đã tải thành công mô hình Qwen LLM!")
        except Exception as e: 
            print(f"LỖI TẢI LLM: {e}")
            self.qwen_llm = None

    def rectify_whole_sign(self, img):
        ocr_res = self.paddle.ocr(img, cls=False, det=True, rec=False)
        if not ocr_res or ocr_res[0] is None or len(ocr_res[0]) < 1: return img

        def order_points(pts):
            rect = np.zeros((4, 2), dtype="float32")
            s = pts.sum(axis=1); rect[0] = pts[np.argmin(s)]; rect[2] = pts[np.argmax(s)]
            diff = np.diff(pts, axis=1); rect[1] = pts[np.argmin(diff)]; rect[3] = pts[np.argmax(diff)]
            return rect

        boxes = [order_points(np.array(b)) for b in ocr_res[0]]
        top_slopes, bot_slopes = [], []
        for b in boxes:
            if b[1][0] != b[0][0]: top_slopes.append((b[1][1] - b[0][1]) / (b[1][0] - b[0][0]))
            if b[2][0] != b[3][0]: bot_slopes.append((b[2][1] - b[3][1]) / (b[2][0] - b[3][0]))

        m_top = np.median(top_slopes) if top_slopes else 0
        m_bot = np.median(bot_slopes) if bot_slopes else 0

        all_pts = np.concatenate(boxes)
        
        width_text = np.max(all_pts[:, 0]) - np.min(all_pts[:, 0])
        height_text = np.max(all_pts[:, 1]) - np.min(all_pts[:, 1])
        
        pad_ratio_x = 0.08 
        pad_ratio_y_bot = 0.15 
        pad_ratio_y_top = 0.2 
        
        pad_x = int(width_text * pad_ratio_x)
        pad_y_bot = int(height_text * pad_ratio_y_bot)
        pad_y_top = int(height_text * pad_ratio_y_top)

        min_x, max_x = np.min(all_pts[:, 0]) - pad_x, np.max(all_pts[:, 0]) + pad_x
        c_top = np.min(all_pts[:, 1] - m_top * all_pts[:, 0]) - pad_y_top
        c_bot = np.max(all_pts[:, 1] - m_bot * all_pts[:, 0]) + pad_y_bot

        tl, tr = [min_x, min_x * m_top + c_top], [max_x, max_x * m_top + c_top]
        br, bl = [max_x, max_x * m_bot + c_bot], [min_x, min_x * m_bot + c_bot]

        if tl[1] >= bl[1] or tr[1] >= br[1]: return img

        src_pts = np.array([tl, tr, br, bl], dtype="float32")
        h_left, h_right = bl[1] - tl[1], br[1] - tr[1]
        h_new, w_new = int(max(h_left, h_right)), int(max_x - min_x)

        ratio = max(h_left, h_right) / (min(h_left, h_right) + 1e-5)
        if 1.1 < ratio < 3.0: w_new = int(w_new * (1.0 + (ratio - 1.0) * 0.55)) 

        if w_new <= 0 or h_new <= 0: return img
        dst_pts = np.array([[0, 0], [w_new, 0], [w_new, h_new], [0, h_new]], dtype="float32")
        try:
            return cv2.warpPerspective(img, cv2.getPerspectiveTransform(src_pts, dst_pts), (w_new, h_new), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        except: return img

    def is_valid_text(self, text):
        return len(text.strip()) >= 2 and bool(re.search(r'[a-zA-Z0-9]', text))

    def enhance_contrast(self, img):
        img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        img_yuv[:,:,0] = clahe.apply(img_yuv[:,:,0])
        return cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

    def binary_threshold(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 15)
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    def sharpen_image(self, img):
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        return cv2.filter2D(img, -1, kernel)

    def grayscale_eq(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(cv2.equalizeHist(gray), cv2.COLOR_GRAY2BGR)

    def extract_info_and_clean_text(self, texts):
        combined = " ".join(texts)
        
        emails = []
        standard_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', combined)
        emails.extend(standard_emails)
        
        fallback_emails = re.findall(r'(?i)\b(?:e-?mail|mail)\s*[:\-]?\s*([a-zA-Z0-9._%+-]+)', combined)
        for pe in fallback_emails:
            if '.' in pe and len(pe) > 5 and '@' not in pe:
                pe_fixed = re.sub(r'[QqAa0O]?\.?(gmail\.com|yahoo\.com|outlook\.com|hotmail\.com|icloud\.com)', r'@\1', pe, flags=re.IGNORECASE)
                if '@' in pe_fixed:
                    emails.append(pe_fixed)
                else:
                    emails.append(pe)
                    
        emails = list(dict.fromkeys(emails))
        
        raw_webs = re.findall(r'\b(?:www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}|[a-zA-Z0-9-]+\.(?:com|vn|net|org)(?:\.[a-zA-Z]{2,})?)\b', combined)
        webs = []
        exclude_mail_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com']
        
        for w in raw_webs:
            w_lower = w.lower()
            if "@" in w: continue
            if any(w_lower == d or w_lower.endswith("@" + d) for d in exclude_mail_domains): continue
            webs.append(w)
            
        webs = list(dict.fromkeys(webs))
        
        return {"email": emails, "website": webs}

    # =========================================================================
    # HÀM DETECT ĐÃ GỘP: Trả về Bounding Box thô từ Paddle hoặc CRAFT
    # =========================================================================
    def detect_robust(self, img, use_craft=False):
        h, w = img.shape[:2]
        sf = min(1.0, 1024 / max(h, w))
        img_s = cv2.resize(img, (int(w*sf), int(h*sf))) if sf < 1.0 else img
        
        raw_boxes = []
        if not use_craft:
            res = self.paddle.ocr(img_s, cls=True, det=True, rec=False)
            if res and res[0]:
                raw_boxes = [np.array(b, dtype="float32") / sf for b in res[0]]
        else:
            if self.easyocr:
                # Chỉ lấy detect box (CRAFT), bỏ qua text và conf
                res = self.easyocr.readtext(img_s, min_size=10)
                if res:
                    raw_boxes = [np.array(item[0], dtype="float32") / sf for item in res]
        
        # MỌI LOGIC PADDING KHUNG SAU KHI NHẬN DIỆN ĐỀU GIỮ NGUYÊN 100% CHO CẢ 2 LUỒNG
        boxes = []
        if raw_boxes:
            for i, box in enumerate(raw_boxes):
                box_h = max(np.linalg.norm(box[0]-box[3]), np.linalg.norm(box[1]-box[2]))
                
                desired_pad_top = box_h * 0.20  
                desired_pad_bot = box_h * 0.10  
                
                top_y = min(box[0][1], box[1][1])
                bot_y = max(box[2][1], box[3][1])
                left_x = min(box[0][0], box[3][0])
                right_x = max(box[1][0], box[2][0])
                
                for j, other_box in enumerate(raw_boxes):
                    if i == j: continue
                    o_top_y = min(other_box[0][1], other_box[1][1])
                    o_bot_y = max(other_box[2][1], other_box[3][1])
                    o_left_x = min(other_box[0][0], other_box[3][0])
                    o_right_x = max(other_box[1][0], other_box[2][0])
                    
                    if not (right_x < o_left_x or left_x > o_right_x):
                        if o_bot_y <= top_y:
                            dist = top_y - o_bot_y
                            desired_pad_top = min(desired_pad_top, max(0, dist - 1.0))
                        elif o_top_y >= bot_y:
                            dist = o_top_y - bot_y
                            desired_pad_bot = min(desired_pad_bot, max(0, dist - 1.0))
                
                new_box = box.copy()
                new_box[0][1] -= desired_pad_top  
                new_box[1][1] -= desired_pad_top  
                new_box[2][1] += desired_pad_bot  
                new_box[3][1] += desired_pad_bot  
                
                boxes.append(new_box)
                
        return boxes

    def fit_line_and_group(self, boxes):
        """
        THUẬT TOÁN ĐỈNH CAO: HYBRID LINE GROUPING (Gom Y - Cắt X - Quét Size)
        """
        if not boxes: return []
        
        # 1. Trích xuất đặc trưng
        infos = []
        for b in boxes:
            pts = np.array(b)
            min_x, max_x = np.min(pts[:, 0]), np.max(pts[:, 0])
            min_y, max_y = np.min(pts[:, 1]), np.max(pts[:, 1])
            cx = (min_x + max_x) / 2.0
            cy = (min_y + max_y) / 2.0
            h = max_y - min_y
            infos.append({'b': b, 'cx': cx, 'cy': cy, 'h': h, 'min_x': min_x, 'max_x': max_x})
            
        # 2. BƯỚC 1: Sắp xếp và gom theo Băng Ngang (Trục Y)
        infos.sort(key=lambda x: x['cy'])
        y_bands = []
        current_band = []
        
        for info in infos:
            if not current_band:
                current_band.append(info)
            else:
                avg_cy = sum(item['cy'] for item in current_band) / len(current_band)
                avg_h = sum(item['h'] for item in current_band) / len(current_band)
                if abs(info['cy'] - avg_cy) <= (max(info['h'], avg_h) * 0.6):
                    current_band.append(info)
                else:
                    y_bands.append(current_band)
                    current_band = [info]
        if current_band:
            y_bands.append(current_band)
            
        # 3. BƯỚC 2: Rà soát Khoảng Trắng & Kích Thước để chẻ Cột/Cụm (Trục X)
        final_lines = []
        for band in y_bands:
            band.sort(key=lambda item: item['cx'])
            current_line = [band[0]]
            
            for i in range(1, len(band)):
                prev_box = current_line[-1]
                curr_box = band[i]
                
                gap = curr_box['min_x'] - prev_box['max_x']
                avg_h = (prev_box['h'] + curr_box['h']) / 2.0
                
                # --- ĐÃ THÊM CẢM BIẾN CHÊNH LỆCH KÍCH THƯỚC (SIZE RATIO) ---
                min_h = min(prev_box['h'], curr_box['h'])
                max_h = max(prev_box['h'], curr_box['h'])
                size_ratio = max_h / (min_h + 1e-5) # Tính tỷ lệ chênh lệch
                
                # ĐIỀU KIỆN CẮT (CHỈ CẦN THỎA 1 TRONG 2):
                # 1. Nếu size lệch nhau gấp 2 lần trở lên -> CẮT! (Không cho chữ bự nuốt chữ nhỏ)
                # 2. Nếu khoảng trắng lớn hơn 1.2 lần chiều cao -> CẮT! (Chia cột)
                if size_ratio > 2.0 or gap > avg_h * 1.2:
                    final_lines.append([item['b'] for item in current_line])
                    current_line = [curr_box]
                else:
                    current_line.append(curr_box)
                    
            if current_line:
                final_lines.append([item['b'] for item in current_line])
                
        return final_lines

    def get_regression_rectified_crop(self, image, line_boxes):
        if not line_boxes: return None, None
        pts = np.concatenate(line_boxes, axis=0)
        tops = np.array([b[0] for b in line_boxes] + [b[1] for b in line_boxes], dtype=np.float32)
        bots = np.array([b[3] for b in line_boxes] + [b[2] for b in line_boxes], dtype=np.float32)
        [vxt, vyt, x0t, y0t] = cv2.fitLine(tops, cv2.DIST_L2, 0, 0.01, 0.01).flatten()
        [vxb, vyb, x0b, y0b] = cv2.fitLine(bots, cv2.DIST_L2, 0, 0.01, 0.01).flatten()
        minx, maxx = np.min(pts[:,0]), np.max(pts[:,0])
        def gy(x, vx, vy, x0, y0): return y0 if abs(vx)<1e-2 else y0+(vy/vx)*(x-x0)
        
        src = np.array([[minx, gy(minx, vxt, vyt, x0t, y0t)], [maxx, gy(maxx, vxt, vyt, x0t, y0t)],
                        [maxx, gy(maxx, vxb, vyb, x0b, y0b)], [minx, gy(minx, vxb, vyb, x0b, y0b)]], dtype="float32")
        wn = np.linalg.norm(src[1]-src[0]); hn = max(np.linalg.norm(src[3]-src[0]), np.linalg.norm(src[2]-src[1]))
        if hn>5000 or wn>5000 or hn<=0 or wn<=0: return None, None
        pw, ph = int(wn*0.05), int(hn*0.2)
        dst = np.array([[pw, ph], [wn+pw, ph], [wn+pw, hn+ph], [pw, hn+ph]], dtype="float32")
        try: return src.astype(int), cv2.warpPerspective(image, cv2.getPerspectiveTransform(src, dst), (int(wn+pw*2), int(hn+ph*2)), flags=cv2.INTER_CUBIC, borderValue=(255,255,255))
        except: return None, None

    def post_process_llm_data(self, ext_json):
        for k in ["BRAND", "SERVICE", "ADDRESS", "PHONE", "O"]:
            if k not in ext_json or not isinstance(ext_json[k], list):
                ext_json[k] = [ext_json.get(k)] if ext_json.get(k) else []
            ext_json[k] = [str(x).strip() for x in ext_json[k] if str(x).strip()]
            ext_json[k] = list(dict.fromkeys(ext_json[k]))
        return ext_json

    def detect_yolo_signs(self, img_path):
        try:
            pil_image = ImageOps.exif_transpose(Image.open(img_path))
            frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        except Exception:
            frame = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

        t0 = time.time()
        # Ép buộc kích thước đầu vào là 640x640
        yolo_res = self.yolo(frame, imgsz=640, verbose=False)
        t_yolo = time.time() - t0

        boxes = []
        if yolo_res[0].boxes:
            for box in yolo_res[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                if conf > 0.7:
                    boxes.append({"coords": (x1, y1, x2, y2), "conf": conf})

        boxes.sort(key=lambda x: x['conf'], reverse=True)
        return frame, boxes, t_yolo

    def regex_pre_extract(self, texts):
        extracted = {"ADDRESS": [], "PHONE": []}
        remaining_texts = []
        
        if not texts:
            return extracted, remaining_texts
            
        all_y = []
        all_h = []
        for t in texts:
            pts = t['box_points'].reshape(-1, 2)
            min_y, max_y = np.min(pts[:, 1]), np.max(pts[:, 1])
            all_y.append(max_y)
            all_h.append(max_y - min_y)
            
        global_max_y = max(all_y) if all_y else 1   
        global_max_h = max(all_h) if all_h else 1   
        
        first_addr_h = None 
        
        phone_prefixes = r'(?:điện thoại(?: liên hệ| di động)?|di động|dđ|tổng đài|cskh|chăm sóc khách hàng|tel|hotline|sđt|sdt|đt|phone|zalo|call|liên hệ|mobi|fax)'
        addr_prefixes = r'(?:đ[iị]a ch[iỉ](?:\s*(?:đkkd|đăng ký kinh doanh|liên hệ|giao dịch))?|đ/c|đc|add(?:ress)?|trụ sở(?: chính)?|cơ sở\s*\d+|chi nhánh\s*\d+|cn[\.\s]*\d+)'        
        phone_pattern = re.compile(rf'(?i)(?:{phone_prefixes}\s*[:\-\.]?\s*)?((?:\+84|0|1800|1900|\(\s*\d{{2,5}}\s*\))(?:(?!\s*[\-,\./]\s*(?:\+84|0|1800|1900)(?:[\s\.\-]*\d){{7}})[ \-\.\d]){{4,15}})(?=\b|[^\d])')

        addr_admin_keywords = re.compile(r'\b(phường|quận|huyện|tỉnh|thành phố|thị xã|thị trấn|tp\.|q\.|p\.|tx\.|h\.|khu phố|kp\.|thôn|ấp|đường|quốc lộ|ql\d*|đại lộ|khu vực|kv|ninh kiều|bình thủy|cái răng|ô môn|thốt nốt|phong điền|cờ đỏ|thới lai|vĩnh thạnh)\b', re.IGNORECASE)
        short_addr_pattern = re.compile(r'^\s*(?:số|lô|kiot|ki-ốt|quầy|tầng|lầu\s+)?(?:[a-zA-Z]+\d+|\d+[a-zA-Z]*)(?:/\d{1,4}[a-zA-Z]?)?\s+[^\W\d_]+\s+[^\W\d_]+', re.IGNORECASE)
        
        addr_prefix_pattern = re.compile(rf'(?i)^{addr_prefixes}\s*[:\-]*\s*')
        exclude_pattern = re.compile(r'^(?:công ty|cty|dntn|doanh nghiệp|nhà thuốc|siêu thị|tạp hóa|trái cây|cửa hàng|đại lý|quán|nhà hàng|trung tâm|bệnh viện|trường|salon|spa|chuyên|phòng khám|shop|store|gara|garage|hotel|khách sạn|nhà nghỉ|văn phòng|vpgd|showroom|kho|xưởng|ủy ban|ubnd|sở|ban|bộ|ngân hàng|doanh trại|tiệm|htx|nha khoa|răng hàm mặt|thẩm mỹ|viện|trạm|chợ|bánh mì|bánh tráng|cơ sở|tòa án|công an|chi cục|tổng cục|đài|nhà văn hóa|đảng bộ|chi bộ|hội đồng|đoàn)\b', re.IGNORECASE)        
        remove_prefix_pattern = re.compile(r'(?i)^(?:đ[iị]a ch[iỉ](?:\s*(?:đkkd|đăng ký kinh doanh|liên hệ|giao dịch))?|đ/c|đc|add(?:ress)?)\s*[:\-]*\s*')

        for text_info in texts:
            current_text = text_info['text'].strip()
            box_coords = text_info['box_points']
            
            pts = box_coords.reshape(-1, 2)
            box_h = np.max(pts[:, 1]) - np.min(pts[:, 1])
            box_y_center = (np.min(pts[:, 1]) + np.max(pts[:, 1])) / 2
            
            matches = list(phone_pattern.finditer(current_text))
            for match in matches:
                full_match_str = match.group(0)
                raw_phone = match.group(1)
                has_phone_prefix = bool(re.search(rf'(?i){phone_prefixes}', full_match_str))
                clean_digits = re.sub(r'[^\d+]', '', raw_phone)
                
                if len(clean_digits) < 8 and not has_phone_prefix:
                    continue 
                extracted["PHONE"].append(clean_digits)
                current_text = current_text.replace(full_match_str, '').strip()
                
            current_text = re.sub(rf'(?i)^{phone_prefixes}?\s*[:\-\.]*\s*$', '', current_text).strip()
            
            if not current_text:
                continue 
                
            is_addr = False
            has_addr_prefix = bool(addr_prefix_pattern.search(current_text))
            
            if has_addr_prefix: 
                is_addr = True
            elif short_addr_pattern.search(current_text): 
                is_addr = True
            elif addr_admin_keywords.search(current_text):
                has_number = bool(re.search(r'\d', current_text))
                has_comma = ',' in current_text
                admin_matches = len(addr_admin_keywords.findall(current_text))
                
                has_province_or_city = bool(re.search(r'\b(tỉnh|thành phố|tp\.)\b', current_text, re.IGNORECASE))
                
                is_small_text = box_h <= global_max_h * 0.6
                is_bottom_half = box_y_center >= global_max_y * 0.5
                
                if (has_number or has_comma or admin_matches >= 2 or has_province_or_city) and (is_small_text or is_bottom_half):
                    is_addr = True
                    
            if is_addr and not has_addr_prefix and first_addr_h is not None:
                if box_h > first_addr_h * 1.8 or box_h < first_addr_h * 0.5:
                    is_addr = False 
                    
            if exclude_pattern.search(current_text) and not has_addr_prefix: 
                is_addr = False

            if is_addr:
                if first_addr_h is None:
                    first_addr_h = box_h 
                    
                clean_addr = remove_prefix_pattern.sub('', current_text).strip()
                clean_addr = re.sub(rf'(?i)(?:{phone_prefixes}).*$', '', clean_addr).strip(' ,.-')
                
                clean_addr = re.sub(r'(?i)^(cn[\.\s]*\d+|cơ sở\s*\d+|chi nhánh\s*\d+)\s*[:\-]+\s*', r'\1: ', clean_addr)
                
                if clean_addr: extracted["ADDRESS"].append(clean_addr)
            else:
                remaining_texts.append({'text': current_text, 'box_points': box_coords})
        
        if extracted["ADDRESS"]:
            final_addrs = []
            for addr in extracted["ADDRESS"]:
                is_duplicate = False
                for i, existing in enumerate(final_addrs):
                    if addr.lower() in existing.lower():
                        is_duplicate = True; break
                    elif existing.lower() in addr.lower():
                        final_addrs[i] = addr
                        is_duplicate = True; break
                if not is_duplicate:
                    final_addrs.append(addr) 
            extracted["ADDRESS"] = [", ".join(final_addrs)]
            
        extracted["PHONE"] = list(dict.fromkeys(extracted["PHONE"]))
        return extracted, remaining_texts

    def process_ocr_llm_generator(self, frame, selected_box, img_path, t_yolo, use_craft=False):
        timings = {'YOLO': t_yolo}
        t_start_total = time.time()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 1. Khởi tạo & Ghi log YOLO
            x1, y1, x2, y2 = selected_box
            write_log(f"\n[LOG STEP 1] YOLO v8 Đã định vị khung biển hiệu: Tọa độ (x1:{x1}, y1:{y1}, x2:{x2}, y2:{y2}) - Tốn: {t_yolo:.3f}s")
            yield {"step": "init", "original_frame": frame, "yolo_box": (x1, y1, x2, y2)}

            sign_crop = frame[y1:y2, x1:x2]
            sign_enhanced = self.enhance_contrast(sign_crop)
            
            # =========================================================================
            # LUỒNG LOGIC TỪ ĐÂY CHẠY GIỐNG NHAU 100% (Cả Nắn Phẳng, Gom Dòng, Cắt Chữ)
            # =========================================================================

            # 2. Rectify 3D TOÀN CỤC (Cả 2 luồng đều dùng) & Ghi log
            t0 = time.time()
            flat_sign = self.rectify_whole_sign(sign_enhanced)
            timings['Rectify_3D'] = time.time() - t0
            write_log(f"[LOG STEP 2] Cân bằng mặt phẳng (Rectify 3D) hoàn tất. Tốn: {timings['Rectify_3D']:.3f}s")
            yield {"step": "yolo", "sign_crop": flat_sign, "time": timings['YOLO'] + timings['Rectify_3D']}

            # 3. Detect (Paddle hoặc CRAFT) và đưa vào Gom dòng chung
            t0 = time.time()
            # Hàm detect_robust đã được thiết kế lại để nhận diện bằng 1 trong 2 luồng 
            # nhưng ĐỀU phải đi qua vòng lặp padding (mở rộng lề) và trả về format giống nhau.
            valid_boxes = [b for b in self.detect_robust(flat_sign, use_craft) if (np.max(b[:,1])-np.min(b[:,1]) > max(15, int(flat_sign.shape[0]*0.015)))]
            
            # Thuật toán Gom Dòng thần thánh hoạt động cho CẢ Paddle và CRAFT!
            lines = self.fit_line_and_group(valid_boxes)
            timings['Det_And_Group'] = time.time() - t0
            
            det_name = "CRAFT (EasyOCR)" if use_craft else "PaddleOCR"
            write_log(f"[LOG STEP 3] {det_name} Det & Gom dòng hoàn tất: Tìm thấy {len(lines)} cụm chữ độc lập. Tốn: {timings['Det_And_Group']:.3f}s")
            yield {"step": "paddle", "time": timings['Det_And_Group']}

            # 4. VietOCR Rec & Ghi log
            t0 = time.time()
            results_data = []
            for idx, line_boxes in enumerate(lines):
                # Hàm cắt và nắn chi tiết được dùng chung
                box_visual, crop_img = self.get_regression_rectified_crop(flat_sign, line_boxes)
                if crop_img is None or crop_img.size == 0: continue
                
                h, w = crop_img.shape[:2]; target_w = max(32, int(w * (64 / h)))
                crop_img = cv2.resize(crop_img, (target_w, 64), interpolation=cv2.INTER_CUBIC)

                best_candidate = {'prob': 0.0, 'text': '', 'name': '', 'img': crop_img}
                filters = [("Original", lambda x: x), ("Sharpen", self.sharpen_image), 
                           ("Gray_Eq", self.grayscale_eq), ("Binary", self.binary_threshold)]
                           
                for fname, func in filters:
                    proc = func(crop_img)
                    pil_input = Image.fromarray(cv2.cvtColor(proc, cv2.COLOR_BGR2RGB))
                    text, prob = self.vietocr.predict(pil_input, return_prob=True)
                    if prob > best_candidate['prob']:
                        best_candidate = {'name': fname, 'text': text, 'prob': prob, 'img': proc}
                    if prob > 0.88: break
                        
                if best_candidate['prob'] > 0.8 and self.is_valid_text(best_candidate['text']):
                    results_data.append({
                        'id': idx + 1, 'box_points': box_visual.reshape((-1, 1, 2)),
                        'straight_img': crop_img, 'final_img': best_candidate['img'],
                        'filter_name': best_candidate['name'], 'text': best_candidate['text'], 'conf': best_candidate['prob']
                    })
                    
            timings['VietOCR_Rec'] = time.time() - t0
            
            write_log("\n" + "="*50)
            write_log(f"[LOG STEP 4] KẾT QUẢ ĐỌC CHỮ (VIETOCR VGG-Transformer):")
            for r in results_data: 
                write_log(f"      + Text: '{r['text']:<35}' | Conf: {r['conf']:.4f} | Filter: {r['filter_name']}")
            write_log("="*50)
            
            yield {"step": "vietocr", "results_data": results_data, "time": timings['VietOCR_Rec']}

            # 5. Qwen LLM & Regex 
            t0 = time.time()
            ext_json = {"BRAND":[],"SERVICE":[],"ADDRESS":[],"PHONE":[],"O":[]}
            remaining_for_llm = []
            
            if results_data and self.qwen_llm:
                regex_extracted, remaining_for_llm = self.regex_pre_extract(results_data)
                ext_json["ADDRESS"].extend(regex_extracted["ADDRESS"])
                ext_json["PHONE"].extend(regex_extracted["PHONE"])
                
                write_log("\n" + "="*50)
                write_log(f"[LOG STEP 5.1] KẾT QUẢ BÓC TÁCH BẰNG REGEX (TRƯỚC LLM):")
                write_log(f"   + Địa chỉ đã gom: {regex_extracted['ADDRESS']}")
                write_log(f"   + SĐT đã gom: {regex_extracted['PHONE']}")
                write_log(f"   + Số dòng dữ liệu còn lại đẩy vào LLM: {len(remaining_for_llm)}")
                write_log("="*50)
                
                if remaining_for_llm:
                    ctx = "\n".join([f"[{int(np.min(r['box_points'][:,0,0]))}, {int(np.min(r['box_points'][:,0,1]))}, {int(np.max(r['box_points'][:,0,0]))}, {int(np.max(r['box_points'][:,0,1]))}] {r['text']}" for r in remaining_for_llm])
                    prompt = f"""Nhiệm vụ: Phân tích các dòng chữ OCR từ biển hiệu và trích xuất vào định dạng JSON. 
Chỉ xuất JSON hợp lệ, các giá trị phải là mảng (Array). Không giải thích.

Các trường cần trích xuất:
- "BRAND": Tên thương hiệu, công ty, cửa hàng. TRÍCH XUẤT ĐẦY ĐỦ loại hình kinh doanh và tên riêng. CHÚ Ý: Nếu biển hiệu có cả tên công ty chủ quản và tên chi nhánh/cửa hàng trực thuộc, hãy GỘP CHUNG tất cả thành 1 giá trị BRAND duy nhất.
- "SERVICE": Các loại hình dịch vụ, ngành nghề, sản phẩm kinh doanh hoặc liên quan tới việc kinh doanh.
- "O": Thông tin phụ, nhiễu: câu slogan, bằng cấp, nhãn hiệu quảng cáo, hoặc các đoạn địa chỉ/số điện thoại thừa bị sót lại.

--- VÍ DỤ ---
Đầu vào OCR:
[50, 20, 800, 60] CÔNG TY TNHH DƯỢC PHẨM TÂY ĐÔ
[100, 80, 750, 150] NHÀ THUỐC HUỲNH LỘC
[200, 160, 600, 200] CHUYÊN BÁN SỈ VÀ LẺ THUỐC TÂY
[120, 220, 400, 250] DSĐH: Tiêu Huỳnh Lộc
[150, 400, 300, 440] Salonpas

Đầu ra JSON:
{{"BRAND": ["CÔNG TY TNHH DƯỢC PHẨM TÂY ĐÔ NHÀ THUỐC HUỲNH LỘC"], "SERVICE": ["CHUYÊN BÁN SỈ VÀ LẺ THUỐC TÂY"], "O": ["DSĐH: Tiêu Huỳnh Lộc", "Salonpas"]}}
-------------

Đầu vào OCR:
{ctx}

Đầu ra JSON:"""
                    
                    inputs = {k: v.to(self.qwen_llm.device) for k, v in self.qwen_tokenizer([self.qwen_tokenizer.apply_chat_template([{"role":"user","content":prompt}], tokenize=False, add_generation_prompt=True)], return_tensors="pt").items()}
                    
                    with torch.no_grad():
                        g_ids = self.qwen_llm.generate(**inputs, max_new_tokens=1024, do_sample=False, pad_token_id=self.qwen_tokenizer.eos_token_id)
                    res_text = self.qwen_tokenizer.batch_decode([g[len(i):] for i, g in zip(inputs["input_ids"], g_ids)], skip_special_tokens=True)[0]
                    
                    write_log("\n" + "="*50)
                    write_log(f"[LOG STEP 5.2] KẾT QUẢ NỘI SUY TỪ QWEN LLM (RAW TEXT):")
                    write_log(res_text)
                    write_log("="*50)

                    try: 
                        start_idx, end_idx = res_text.find('{'), res_text.rfind('}')
                        if start_idx != -1 and end_idx != -1:
                            llm_json = json.loads(res_text[start_idx:end_idx+1])
                            for k in ["BRAND", "SERVICE", "O"]:
                                if k in llm_json:
                                    val = llm_json[k]
                                    if isinstance(val, list): ext_json[k].extend(val)
                                    elif isinstance(val, str): ext_json[k].append(val)
                    except: pass
                        
            ext_json = self.post_process_llm_data(ext_json)
            
            if not ext_json.get("BRAND") and not ext_json.get("SERVICE"):
                if remaining_for_llm:
                    fallback_text = " ".join([r['text'] for r in remaining_for_llm]).strip()
                    if fallback_text: ext_json["SERVICE"] = [fallback_text]

            write_log("\n" + "="*50)
            write_log(f"[LOG STEP 5.3] KẾT QUẢ JSON SAU CÙNG (GỘP REGEX + LLM):")
            write_log(json.dumps(ext_json, ensure_ascii=False, indent=4))
            write_log("="*50)
                
            timings['LLM_Qwen'] = time.time() - t0
            yield {"step": "llm", "extracted_json": ext_json, "time": timings['LLM_Qwen']}

            # 6. Classifier (Linear SVC)
            t0 = time.time()
            cat = "Chưa xác định"
            text_input = ""
            text_segmented = ""
            
            if results_data and self.classifier:
                br = " ".join(ext_json.get("BRAND", [])).lower()
                sr = " ".join(ext_json.get("SERVICE", [])).lower()
                
                if br or sr:
                    text_input = f"{br} {sr}".strip()
                    text_segmented = word_tokenize(text_input, format="text")
                    cat = str(self.classifier.predict([text_segmented])[0])
                else: 
                    cat = "Thiếu dữ liệu"
                    
            timings['Classifier'] = time.time() - t0
            
            write_log("\n" + "="*50)
            write_log(f"[LOG STEP 6] PHÂN LOẠI DANH MỤC (LINEAR SVC):")
            if text_input:
                write_log(f"   + Text gộp thô (BRAND + SERVICE): '{text_input}'")
                write_log(f"   + Text qua UnderTheSea tách từ : '{text_segmented}'")
            write_log(f"   + Kết quả phân loại cuối cùng  : {cat}")
            write_log(f"   + Thời gian: {timings['Classifier']:.3f}s")
            write_log("="*50)
            
            yield {"step": "classifier", "category": cat, "time": timings['Classifier']}

            timings['Total'] = t_yolo + (time.time() - t_start_total)
            yield {"step": "done", "info": self.extract_info_and_clean_text([r['text'] for r in results_data]), "timings": timings}


# ==============================================================================
# GIAO DIỆN NGƯỜI DÙNG (UI)
# ==============================================================================
class OCRInspectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Công cụ trích xuất từ biển hiệu (Có Toggle CRAFT/Paddle - Unified Logic)")
        self.root.geometry("1450x850")
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", font=('Consolas', 11), rowheight=28)
        style.configure("Treeview.Heading", font=('Arial', 11, 'bold'))
        style.map('Treeview', background=[('selected', '#0078D7')], foreground=[('selected', 'white')])
        self.root.option_add("*TTreeview*highlightThickness", 0)

        self.backend = OCRBackend()
        self.current_results = []
        self.current_flat_sign = None

        self.build_ui()
        self.progress_queue = queue.Queue()

    def build_ui(self):
        top_frame = tk.Frame(self.root, bg="#2C3E50", height=60)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        top_frame.pack_propagate(False)
        
        title_lbl = tk.Label(top_frame, text="AI SIGNBOARD INSPECTOR", font=("Impact", 24), bg="#2C3E50", fg="white")
        title_lbl.pack(side=tk.LEFT, padx=20)
        
        self.lbl_status = tk.Label(top_frame, text="Sẵn sàng", font=("Arial", 12, "bold"), bg="#2C3E50", fg="#2ECC71")
        self.lbl_status.pack(side=tk.RIGHT, padx=20)

        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = tk.Frame(paned, width=500, bg="#ecf0f1")
        paned.add(left_frame, weight=1)

        # ----------------------------------------------------
        # BẢNG ĐIỀU KHIỂN LUỒNG (TOGGLE SWITCH)
        # ----------------------------------------------------
        toggle_frame = tk.Frame(left_frame, bg="#ecf0f1")
        toggle_frame.pack(fill=tk.X, padx=10, pady=(15, 5))
        
        tk.Label(toggle_frame, text="Luồng xử lý OCR (Detector):", font=("Arial", 11, "bold"), bg="#ecf0f1").pack(side=tk.LEFT)
        
        self.use_craft_var = tk.BooleanVar(value=False)
        
        self.btn_toggle = tk.Button(toggle_frame, text="PADDLE OCR (Mặc định)", font=("Arial", 11, "bold"),
                                    bg="#34495e", fg="white", relief=tk.FLAT, command=self.toggle_pipeline, width=22)
        self.btn_toggle.pack(side=tk.RIGHT)
        # ----------------------------------------------------

        self.btn_select = tk.Button(left_frame, text="CHỌN ẢNH XỬ LÝ", command=self.load_image_trigger, 
                                    font=("Arial", 12, "bold"), bg="#3498db", fg="white", height=2, relief=tk.FLAT, cursor="hand2")
        self.btn_select.pack(fill=tk.X, padx=10, pady=10)

        cat_frame = ttk.LabelFrame(left_frame, text=" Tổng Quan Biển Hiệu ")
        cat_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_category = tk.Label(cat_frame, text="LOẠI HÌNH: ...", font=("Arial", 14, "bold"), fg="#c0392b")
        self.lbl_category.pack(anchor="w", padx=10, pady=15)

        info_frame = ttk.LabelFrame(left_frame, text=" Dữ liệu Trích xuất (LLM + Regex Final) ")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        labels = [("🏢 Thương hiệu:", "lbl_brand", "#d35400"), 
                  ("🛠 Dịch vụ:", "lbl_service", "#2980b9"),
                  ("📞 Điện thoại:", "lbl_phone", "#16a085"),
                  ("🏠 Địa chỉ OCR:", "lbl_addr", "#8e44ad"),
                  ("✉ Liên hệ khác:", "lbl_contact", "black")]
        
        self.info_vars = {}
        for row, (text, var_name, color) in enumerate(labels):
            tk.Label(info_frame, text=text, font=("Arial", 10, "bold"), fg=color).grid(row=row, column=0, sticky="w", padx=10, pady=6)
            val_lbl = tk.Label(info_frame, text="...", font=("Arial", 10), wraplength=320, justify="left")
            val_lbl.grid(row=row, column=1, sticky="w", pady=6)
            self.info_vars[var_name] = val_lbl

        ocr_frame = ttk.LabelFrame(left_frame, text=" Danh sách Dòng chữ (Click/Phím Lên Xuống để xem) ")
        ocr_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tree = ttk.Treeview(ocr_frame, columns=("ID", "Conf", "Text"), show="headings")
        self.tree.heading("ID", text="#")
        self.tree.heading("Conf", text="Độ tin cậy")
        self.tree.heading("Text", text="Văn bản nhận diện")
        
        self.tree.column("ID", width=30, anchor="center")
        self.tree.column("Conf", width=80, anchor="center")
        self.tree.column("Text", width=350, anchor="w")
        
        tree_scroll_y = ttk.Scrollbar(ocr_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x = ttk.Scrollbar(ocr_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.tree.tag_configure('highlighted', background='#ffeaa7', font=('Consolas', 11, 'bold'))
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        right_frame = tk.Frame(paned, bg="white")
        paned.add(right_frame, weight=3)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_orig = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_orig, text=" [1] Ảnh Gốc & Khung YOLO ")
        self.canvas_orig = ZoomableCanvas(self.tab_orig)
        self.canvas_orig.pack(fill=tk.BOTH, expand=True)

        self.tab_rect = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_rect, text=" [2] Biển Hiệu (Nắn phẳng 3D) ")
        self.canvas_rect = ZoomableCanvas(self.tab_rect)
        self.canvas_rect.pack(fill=tk.BOTH, expand=True)

        self.tab_line = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_line, text=" [3] Trích xuất Dòng (OCR Input) ")
        
        lbl_instruct = tk.Label(self.tab_line, text=" Hãy nhấp vào một dòng trong bảng OCR bên trái để xem chi tiết ảnh cắt.", font=("Arial", 11, "italic"), fg="gray")
        lbl_instruct.pack(pady=5)
        
        detail_frame = ttk.LabelFrame(self.tab_line, text=" Phân tích chi tiết OCR ")
        detail_frame.pack(fill=tk.X, padx=20, pady=5)
        
        meta_frame = tk.Frame(detail_frame)
        meta_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_detail_conf = tk.Label(meta_frame, text="Độ tin cậy: ...", font=("Arial", 12, "bold"), fg="#27ae60")
        self.lbl_detail_conf.pack(side=tk.LEFT, padx=(0, 20))
        
        self.lbl_detail_filter = tk.Label(meta_frame, text="Bộ lọc sử dụng: ...", font=("Arial", 12, "bold"), fg="#2980b9")
        self.lbl_detail_filter.pack(side=tk.LEFT)
        
        self.txt_detail_text = tk.Text(detail_frame, height=3, font=("Consolas", 14), wrap=tk.WORD, bg="#fdfbfb", relief=tk.SOLID, bd=1)
        self.txt_detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.txt_detail_text.config(state=tk.DISABLED)

        img_paned = ttk.PanedWindow(self.tab_line, orient=tk.VERTICAL)
        img_paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        frame_orig = ttk.LabelFrame(img_paned, text=" Hình cắt thô (Original Crop) ")
        self.canvas_crop_orig = ZoomableCanvas(frame_orig)
        self.canvas_crop_orig.pack(fill=tk.BOTH, expand=True)
        img_paned.add(frame_orig, weight=1)

        frame_proc = ttk.LabelFrame(img_paned, text=" Hình đã qua Tiền xử lý (Đưa vào VietOCR) ")
        self.canvas_crop_proc = ZoomableCanvas(frame_proc)
        self.canvas_crop_proc.pack(fill=tk.BOTH, expand=True)
        img_paned.add(frame_proc, weight=1)

    def toggle_pipeline(self):
        if self.use_craft_var.get():
            self.use_craft_var.set(False)
            self.btn_toggle.config(text="PADDLE OCR (Mặc định)", bg="#34495e")
        else:
            self.use_craft_var.set(True)
            self.btn_toggle.config(text="CRAFT (Từ EasyOCR)", bg="#e67e22")

    def format_val(self, val):
        if not val: return "Không tìm thấy"
        if isinstance(val, list):
            val = [str(v).strip() for v in val if str(v).strip()]
            if not val: return "Không tìm thấy"
            return str(val[0]) if len(val) == 1 else "\n".join(f"- {v}" for v in val)
        return str(val)

    def load_image_trigger(self):
        path = filedialog.askopenfilename(filetypes=[("Image", "*.jpg;*.png;*.jpeg")])
        if not path: return
        
        self.btn_select.config(state=tk.DISABLED, bg="#95a5a6", text="ĐANG QUÉT YOLO...")
        self.tree.delete(*self.tree.get_children())
        self.lbl_category.config(text="LOẠI HÌNH: Đang chờ...")
        for k in self.info_vars: self.info_vars[k].config(text="...")
        
        self.canvas_orig.clear(); self.canvas_rect.clear()
        if hasattr(self, 'canvas_crop_orig'):
            self.canvas_crop_orig.clear(); self.canvas_crop_proc.clear()
            
        self.txt_detail_text.config(state=tk.NORMAL)
        self.txt_detail_text.delete(1.0, tk.END)
        self.txt_detail_text.config(state=tk.DISABLED)
        self.lbl_detail_conf.config(text="Độ tin cậy: ...")
        self.lbl_detail_filter.config(text="Bộ lọc sử dụng: ...")
        
        self.notebook.select(0)
        self.lbl_status.config(text="Đang quét biển hiệu...", fg="#f39c12")
        
        threading.Thread(target=self.run_yolo_worker, args=(path,), daemon=True).start()
        self.root.after(100, self.check_queue_and_update_ui)

    def run_yolo_worker(self, path):
        file_name = os.path.basename(path)
        use_craft = self.use_craft_var.get()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        write_log("\n\n" + "★"*60)
        write_log(f"▶ BẮT ĐẦU PHIÊN KIỂM THỬ MỚI (V8 - UNIFIED LOGIC)")
        write_log(f"▷ Luồng Detector sử dụng: {'CRAFT (EasyOCR)' if use_craft else 'PADDLE OCR'}")
        write_log(f"▷ Thời gian thực hiện: {current_time}")
        write_log(f"▷ Tên ảnh kiểm thử: {file_name}")
        write_log("★"*60)
        
        try:
            frame, boxes, t_yolo = self.backend.detect_yolo_signs(path)
            if not boxes:
                self.progress_queue.put({"step": "failed", "msg": "Không tìm thấy biển hiệu nào độ tin cậy > 70%"})
                return
            
            if len(boxes) == 1:
                sel_box = boxes[0]["coords"]
                for progress in self.backend.process_ocr_llm_generator(frame, sel_box, path, t_yolo, use_craft):
                    self.progress_queue.put(progress)
            else:
                self.progress_queue.put({"step": "yolo_selection", "frame": frame, "boxes": boxes, "path": path, "t_yolo": t_yolo})
                
        except Exception as e:
            self.progress_queue.put({"step": "error", "msg": str(e)})

    def run_ocr_pipeline_worker(self, frame, sel_box, path, t_yolo):
        use_craft = self.use_craft_var.get()
        try:
            for progress in self.backend.process_ocr_llm_generator(frame, sel_box, path, t_yolo, use_craft):
                self.progress_queue.put(progress)
        except Exception as e:
            self.progress_queue.put({"step": "error", "msg": str(e)})

    def show_yolo_selection(self, frame, boxes, path, t_yolo):
        vis_frame = frame.copy()
        for i, b in enumerate(boxes):
            x1, y1, x2, y2 = b["coords"]
            cv2.rectangle(vis_frame, (x1, y1), (x2, y2), (0, 0, 255), 4)
            cv2.putText(vis_frame, f"ID {i+1} ({b['conf']*100:.1f}%)", (x1, max(20, y1-15)), cv2.FONT_HERSHEY_SIMPLEX, max(1, vis_frame.shape[1]/1000), (0, 0, 255), max(2, int(vis_frame.shape[1]/500)))

        self.notebook.select(0)
        self.canvas_orig.load_cv2_image(vis_frame)
        self.lbl_status.config(text="Đang chờ bạn chọn biển hiệu cần xử lý...", fg="#f39c12")

        sel_win = tk.Toplevel(self.root)
        sel_win.title("Chọn Biển Hiệu")
        sel_win.geometry("380x300")
        sel_win.transient(self.root)
        sel_win.grab_set() 
        
        def on_close():
            sel_win.destroy()
            self.lbl_status.config(text="Đã hủy thao tác", fg="#e74c3c")
            self.btn_select.config(state=tk.NORMAL, bg="#3498db", text="CHỌN ẢNH XỬ LÝ")
            
        sel_win.protocol("WM_DELETE_WINDOW", on_close)

        tk.Label(sel_win, text="Tìm thấy các biển hiệu (Conf > 70%):", font=("Arial", 11, "bold")).pack(pady=10)

        var_choice = tk.IntVar(value=0)
        list_frame = tk.Frame(sel_win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        for i, b in enumerate(boxes):
            tk.Radiobutton(list_frame, text=f"Biển hiệu số {i+1} (Độ tin cậy: {b['conf']*100:.1f}%)", variable=var_choice, value=i, font=("Arial", 11)).pack(anchor="w", pady=2)

        def on_confirm():
            sel_idx = var_choice.get()
            sel_box = boxes[sel_idx]["coords"]
            sel_win.destroy()
            self.btn_select.config(text="ĐANG XỬ LÝ...")
            threading.Thread(target=self.run_ocr_pipeline_worker, args=(frame, sel_box, path, t_yolo), daemon=True).start()
            self.root.after(100, self.check_queue_and_update_ui)

        tk.Button(sel_win, text="Xác Nhận Xử Lý", command=on_confirm, bg="#27ae60", fg="white", font=("Arial", 11, "bold"), height=2).pack(fill=tk.X, padx=30, pady=15)

    def check_queue_and_update_ui(self):
        try:
            while not self.progress_queue.empty():
                progress = self.progress_queue.get_nowait()
                step = progress.get("step")
                
                if step == "error" or step == "failed":
                    self.lbl_status.config(text=f"LỖI: {progress.get('msg')}", fg="#e74c3c")
                    self.btn_select.config(state=tk.NORMAL, bg="#3498db", text="CHỌN ẢNH XỬ LÝ")
                    return
                
                elif step == "yolo_selection":
                    self.show_yolo_selection(progress["frame"], progress["boxes"], progress["path"], progress["t_yolo"])
                    return 

                elif step == "init":
                    orig = progress['original_frame'].copy()
                    x1, y1, x2, y2 = progress['yolo_box']
                    cv2.rectangle(orig, (x1, y1), (x2, y2), (0, 255, 0), 4)
                    cv2.putText(orig, "Selected", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    self.btn_select.config(text="ĐANG XỬ LÝ...")

                    self.notebook.select(0)
                    self.root.update_idletasks()
                    self.canvas_orig.load_cv2_image(orig)
                    self.lbl_status.config(text="[1/5] Đang nắn phẳng phối cảnh...", fg="#f39c12")
                    
                elif step == "yolo":
                    self.current_flat_sign = progress["sign_crop"]
                    self.notebook.select(1)
                    self.root.update_idletasks() 
                    self.canvas_rect.load_cv2_image(self.current_flat_sign)
                    self.lbl_status.config(text="[2/5] Đang gom khung dòng chữ...", fg="#f39c12")
                    
                elif step == "paddle":
                    self.lbl_status.config(text="[3/5] Đang đọc chữ bằng VietOCR...", fg="#f39c12")
                    
                elif step == "vietocr":
                    self.current_results = progress["results_data"]
                    for idx, res in enumerate(self.current_results):
                        self.tree.insert("", tk.END, iid=str(idx), values=(res['id'], f"{res['conf']:.2f}", res['text']))
                    self.lbl_status.config(text="[4/5] Đang bóc tách ý nghĩa (Qwen LLM)...", fg="#f39c12")
                    
                elif step == "llm":
                    js = progress["extracted_json"]
                    self.info_vars["lbl_brand"].config(text=self.format_val(js.get('BRAND')))
                    self.info_vars["lbl_service"].config(text=self.format_val(js.get('SERVICE')))
                    self.info_vars["lbl_phone"].config(text=self.format_val(js.get('PHONE')))
                    self.info_vars["lbl_addr"].config(text=self.format_val(js.get('ADDRESS')))
                    self.lbl_status.config(text="[5/5] Đang phân loại danh mục...", fg="#f39c12")
                    
                elif step == "classifier":
                    self.lbl_category.config(text=f"LOẠI HÌNH: {progress['category'].upper()}")
                    
                elif step == "done":
                    info = progress["info"]

                    contact_str = []
                    if info.get('email'): contact_str.append(f"Email: {self.format_val(info.get('email'))}")
                    if info.get('website'): contact_str.append(f"Web: {self.format_val(info.get('website'))}")
                    self.info_vars["lbl_contact"].config(text=" | ".join(contact_str) if contact_str else "Không tìm thấy")

                    timings = progress.get("timings", {})
                    write_log("\n" + "="*45)
                    write_log("  THỐNG KÊ THỜI GIAN XỬ LÝ (GIÂY):")
                    for stage, t in timings.items():
                        if stage != "Total": write_log(f"   + {stage:<15}: {t:.3f}s")
                    write_log("-" * 45)
                    
                    total_time = timings.get('Total', 0)
                    write_log(f"   => TỔNG CỘNG     : {total_time:.3f}s")
                    write_log("="*45 + "\n")

                    self.lbl_status.config(text=f" HOÀN TẤT XỬ LÝ! (Tổng: {total_time:.2f}s)", fg="#2ecc71")
                    self.btn_select.config(state=tk.NORMAL, bg="#3498db", text="CHỌN ẢNH KHÁC")
                    return 
                    
        except queue.Empty: pass 
        self.root.after(100, self.check_queue_and_update_ui)

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items: return
        
        for item in self.tree.get_children():
            self.tree.item(item, tags=())
            
        item = selected_items[0]
        self.tree.item(item, tags=('highlighted',))
        
        idx = int(item)
        if idx >= len(self.current_results): return
        
        data = self.current_results[idx]
        
        self.notebook.select(2)
        self.root.update_idletasks()

        viz_sign = self.current_flat_sign.copy()
        rect = cv2.minAreaRect(data['box_points'])
        box = np.int0(cv2.boxPoints(rect))
        cv2.drawContours(viz_sign, [box], 0, (0, 0, 255), 4) 
        self.canvas_rect.load_cv2_image(viz_sign)
        
        self.canvas_crop_orig.load_cv2_image(data['straight_img'])
        self.canvas_crop_proc.load_cv2_image(data['final_img'])
        
        self.lbl_detail_conf.config(text=f"Độ tin cậy: {data['conf']:.2f}")
        self.lbl_detail_filter.config(text=f"Bộ lọc sử dụng: {data['filter_name']}")
        
        self.txt_detail_text.config(state=tk.NORMAL)
        self.txt_detail_text.delete(1.0, tk.END)
        self.txt_detail_text.insert(tk.END, data['text'])
        self.txt_detail_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRInspectorApp(root)
    root.mainloop()
import easyocr
import numpy as np
from PIL import Image

# 初始化 EasyOCR Reader (只需要執行一次)
# 指定辨識英文 (包含數字)
# gpu=False 可以強制使用 CPU，如果您的環境沒有 CUDA 或想避免 GPU 問題
reader = easyocr.Reader(['en'], gpu=False) # 或者 gpu=True

def _extract_text_from_image(img_crop):
    """使用 EasyOCR 從裁切後的圖片中提取文字。"""
    try:
        # 將 PIL Image 轉換為 NumPy 陣列
        img_np = np.array(img_crop)

        # 使用 EasyOCR 辨識文字，限制只辨識數字
        # detail=0 只返回文字，更快； paragraph=False 處理單行
        results = reader.readtext(img_np, allowlist='0123456789', detail=0, paragraph=False)

        # 合併所有辨識到的文字片段 (通常應該只有一個)
        extracted_text = "".join(results).strip()
        # 嘗試轉換為整數，如果失敗則返回原始字串或空字串
        try:
            return int(extracted_text)
        except ValueError:
            return extracted_text # 或者返回 None 或保持原樣
    except Exception as e:
        print(f"EasyOCR 辨識時發生錯誤: {e}")
        return None # 返回 None 表示錯誤或未辨識

def getMilitaryText(img):
    militaryCrop = img.crop((480, 159, 581, 200))  # 左,上,右,下
    return _extract_text_from_image(militaryCrop)

def getTradeText(img):
    tradeCrop = img.crop((487, 225, 576, 264))  # 左,上,右,下
    return _extract_text_from_image(tradeCrop)

def getTechText(img):
    techCrop = img.crop((486, 286, 576, 325))  # 左,上,右,下
    return _extract_text_from_image(techCrop)

def getCultureText(img):
    cultureCrop = img.crop((489, 349, 579, 386))  # 左,上,右,下
    return _extract_text_from_image(cultureCrop)

def getAllProperties(img):
    """提取所有屬性並返回一個字典。"""
    properties = {
        "Military": getMilitaryText(img),
        "Trade": getTradeText(img),
        "Tech": getTechText(img),
        "Culture": getCultureText(img)
    }
    return properties 
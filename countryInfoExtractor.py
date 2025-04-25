import pytesseract
from PIL import Image

# 在 Windows 上明確指定 Tesseract 路徑
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # 請確認這是您實際的安裝路徑

def getMilitaryText(img):
    militaryCrop = img.crop((480, 159, 581, 200))  # 左,上,右,下
    config = '--psm 7 -c tessedit_char_whitelist=0123456789'
    militaryText = pytesseract.image_to_string(militaryCrop, config=config)
    print("軍事力 Military:", militaryText.strip())

def getTradeText(img):
    tradeCrop = img.crop((487, 225, 576, 264))  # 左,上,右,下
    config = '--psm 7 -c tessedit_char_whitelist=0123456789'
    tradeText = pytesseract.image_to_string(tradeCrop, config=config)
    print("商業 Trade:", tradeText.strip())

def getTechText(img):
    techCrop = img.crop((486, 286, 576, 325))  # 左,上,右,下
    config = '--psm 7 -c tessedit_char_whitelist=0123456789'
    techText = pytesseract.image_to_string(techCrop, config=config)
    print("科技 Tech:", techText.strip())

def getCultureText(img):
    cultureCrop = img.crop((489, 349, 579, 386))  # 左,上,右,下
    config = '--psm 7 -c tessedit_char_whitelist=0123456789'
    cultureText = pytesseract.image_to_string(cultureCrop, config=config)
    print("文化 Culture:", cultureText.strip())

def getAllProperties(img):
    getMilitaryText(img)
    getTradeText(img)
    getTechText(img)
    getCultureText(img) 
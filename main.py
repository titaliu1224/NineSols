import datetime
from io import BytesIO

import requests
from PIL import Image

from countryInfoExtractor import getAllProperties


def preprocess_image(img, threshold=128):
    """將圖片轉換為灰階並進行二值化處理。"""
    # 1. 轉換為灰階
    gray_img = img.convert('L')
    # 2. 二值化
    binary_img = gray_img.point(lambda p: p > threshold and 255)
    return binary_img

def main():
    # 圖片 URL 列表
    image_urls = [
        "https://cdn.discordapp.com/attachments/1362649898977333360/1365345453616660652/CountryState_Yiguo.png?ex=680cf88b&is=680ba70b&hm=88e867809d6c83d1824ac227e2e4c9aa6702e87b0001784d48950299eee16ef5&",
        "https://cdn.discordapp.com/attachments/1362649898977333360/1365344598624309389/CountryState_Yumin.png?ex=680cf7bf&is=680ba63f&hm=5cef14a43dae56df83b0363230c5b15cf5f9c10ff8a632aa7ce28e1fe787a958&"
        # "請在此處加入更多圖片 URL"
        # "例如: https://example.com/another_image.jpg"
    ]

    for url in image_urls:
        try:
            # 從 URL 提取檔案名稱
            filename = url.split('/')[-1].split('?')[0]
            print(f"--- 正在處理圖片: {filename} ---")

            response = requests.get(url, timeout=10) # 加入超時
            response.raise_for_status() # 檢查請求是否成功

            img = Image.open(BytesIO(response.content))

            # 進行圖片預處理
            processed_img = preprocess_image(img) # 可以傳遞不同的閾值: preprocess_image(img, threshold=150)

            # (可選) 儲存二值化後的圖片以供檢查
            processed_img.save(f"binary_{filename}.png") # 建議指定 .png 以避免潛在問題

            getAllProperties(processed_img) # 將處理後的圖片傳遞給 OCR 函式
            print("-----------------------------------")

        except requests.exceptions.RequestException as e:
            print(f"下載圖片時發生錯誤 {url}: {e}")
        except Exception as e:
            print(f"處理圖片時發生錯誤 {url}: {e}")

if __name__ == "__main__":
    main()
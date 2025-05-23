import datetime
import json  # 引入 json 模組
import os  # 引入 os 模組
import time  # 引入 time 模組
from io import BytesIO

import gspread
import pytz  # 引入 pytz 用於時區處理
import requests
from google.oauth2.service_account import Credentials
from PIL import Image

from countryInfoExtractor import getAllProperties
from selfBotExecutor import get_discord_images_sync  # 引入從 Discord 獲取圖片的函數

# --- Google Sheets 設定 ---
# 優先從環境變數讀取憑證內容 (用於 GitHub Actions)
# 否則，從本地檔案讀取 (用於本地測試)
CREDENTIALS_JSON_CONTENT = os.environ.get('GOOGLE_CREDENTIALS_JSON')
CREDENTIALS_FILE = 'nine-sols-754f9adc71aa.json'

# --- Google Sheets 設定 ---
# 確保這個 JSON 檔案與您的 main.py 在同一個目錄，或者提供完整路徑
CREDENTIALS_FILE = 'nine-sols-754f9adc71aa.json'
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1_dQZCbZjqBTNgXKay_zd3YrxaDvuH5uu4Hz7-wLCI6g/edit?usp=sharing' # <-- Google Sheet 的 URL
SPREADSHEET_NAME = '《 九日 | 混元萬劫 》奄國 | 國民能力表及任務列表' # <-- 用於顯示，可選
WORKSHEET_NAME = 'Logs' # <-- 通常是 'Sheet1'，如果您的工作表名稱不同請修改

# Google API 的範圍
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]
# --- Google Sheets 設定結束 ---

# --- 定義 UTC+8 時區 ---
UTC8 = pytz.timezone('Asia/Shanghai') # 或者 'Asia/Taipei', 'Asia/Hong_Kong' 等

def preprocess_image(img, threshold=128):
    """將圖片轉換為灰階並進行二值化處理。"""
    gray_img = img.convert('L')
    binary_img = gray_img.point(lambda p: p > threshold and 255)
    return binary_img

def get_current_utc8_time_str():
    """獲取當前 UTC+8 時間並格式化為字符串"""
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    utc8_now = utc_now.astimezone(UTC8)
    return utc8_now.strftime("%Y-%m-%d %H:%M:%S")

def main():
    # --- Google Sheets 驗證與開啟 ---
    try:
        creds = None
        if CREDENTIALS_JSON_CONTENT:
            print("正在從環境變數載入 Google 憑證...")
            # 將 JSON 字串轉換為字典
            creds_dict = json.loads(CREDENTIALS_JSON_CONTENT)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        elif os.path.exists(CREDENTIALS_FILE):
            print(f"正在從本地檔案 '{CREDENTIALS_FILE}' 載入 Google 憑證...")
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        else:
            print(f"錯誤：找不到 Google 憑證。請確保 '{CREDENTIALS_FILE}' 存在於本地，或已設定 'GOOGLE_CREDENTIALS_JSON' 環境變數。")
            return

        gc = gspread.authorize(creds)
        # 使用 URL 開啟 Sheet
        sh = gc.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet(WORKSHEET_NAME)
        print(f"成功連接到 Google Sheet (透過 URL): '{sh.title}' -> '{worksheet.title}'")

        # 檢查標頭是否存在，如果不存在則寫入
        header = ["國家", "軍事", "商業", "科技", "文化", "更新時間"]
        first_row = worksheet.row_values(1)
        if not first_row or first_row != header: # 檢查是否為空或不匹配
            # 如果第一行不為空但與期望標頭不同，先刪除第一行再插入新標頭
            if first_row:
                worksheet.delete_rows(1)
                print("已刪除舊標頭行。")
            worksheet.insert_row(header, 1)
            print("已寫入標頭到 Google Sheet")

    except FileNotFoundError: # 這個錯誤現在只會在嘗試讀取本地檔案但不存在時發生
        print(f"錯誤：找不到憑證檔案 '{CREDENTIALS_FILE}'。請確保檔案存在且路徑正確。")
        return
    except json.JSONDecodeError:
        print("錯誤：解析環境變數 'GOOGLE_CREDENTIALS_JSON' 中的 JSON 內容失敗。請檢查 GitHub Secrets 中的值是否為有效的 JSON。")
        return
    except gspread.exceptions.APIError as e:
        # 更具體地處理權限或 API 未啟用的錯誤
        if e.response.status_code == 403:
            print(f"錯誤：權限不足或 API 未啟用。請確保服務帳戶已共享至 Sheet ('{SPREADSHEET_URL}') 並具有編輯權限，且 Google Drive API 和 Sheets API 已啟用。錯誤詳情: {e}")
        else:
            print(f"連接 Google Sheets 時發生 API 錯誤: {e}")
        return
    except gspread.exceptions.SpreadsheetNotFound:
        # 這個錯誤現在不太可能發生，因為 URL 通常是唯一的
        print(f"錯誤：透過 URL '{SPREADSHEET_URL}' 找不到 Google Sheet。請確認 URL 正確且服務帳戶有權限存取。")
        return
    except gspread.exceptions.WorksheetNotFound:
        print(f"錯誤：在 '{sh.title if 'sh' in locals() else SPREADSHEET_URL}' 中找不到名為 '{WORKSHEET_NAME}' 的工作表。")
        return
    except Exception as e:
        print(f"連接 Google Sheets 時發生未預期的錯誤: {e}")
        return
    # --- Google Sheets 驗證與開啟結束 ---

    # 從 Discord 獲取圖片 URL，因為 Discord 的 URL 會過期
    print("正在從 Discord 獲取最新圖片 URL...")
    success, discord_urls = get_discord_images_sync()
    
    if not success or not discord_urls:
        print("錯誤：無法從 Discord 獲取圖片 URL")
        return  # 如果無法獲取 URL，終止程序
    
    print(f"成功從 Discord 獲取了 {len(discord_urls)} 個圖片 URL")
    
    # 使用從 Discord 獲取的 URL
    image_urls = discord_urls

    failed_urls = [] # 記錄第一輪處理失敗的 URL

    print("--- 開始第一輪圖片處理 ---")
    for url in image_urls:
        try:
            base_filename = url.split('/')[-1].split('?')[0]
            filename = base_filename.removeprefix("CountryState_").removesuffix(".png")
            print(f"--- 正在處理 (第一輪): {filename} ---")

            # 下載圖片
            response = requests.get(url, timeout=15) # 增加超時時間
            response.raise_for_status() # 檢查 HTTP 錯誤

            # 處理圖片
            img = Image.open(BytesIO(response.content))
            processed_img = preprocess_image(img)

            # 獲取屬性字典
            properties = getAllProperties(processed_img)
            print(f"  提取結果 (第一輪): {properties}")

            # 準備要寫入 Google Sheet 的行數據
            timestamp = get_current_utc8_time_str() # 使用 UTC+8 時間
            row_data = [
                filename,
                properties.get("Military", ""),
                properties.get("Trade", ""),
                properties.get("Tech", ""),
                properties.get("Culture", ""),
                timestamp
            ]

            # 將數據附加到 Google Sheet
            worksheet.append_row(row_data, value_input_option='USER_ENTERED')
            print(f"  數據已寫入 Google Sheet: {row_data}")
            print("-----------------------------------")

            # 短暫暫停
            time.sleep(1.5)

        except requests.exceptions.RequestException as e:
            print(f"  下載圖片時發生錯誤 (第一輪) {url}: {e}")
            failed_urls.append(url) # 記錄失敗的 URL
            continue # 繼續處理下一個 URL
        except Exception as e:
            # 捕捉圖片處理 (PIL, easyocr) 或 getAllProperties 的錯誤
            # 但排除 Google Sheet 的錯誤 (gspread exceptions 在主 try 外處理)
            if not isinstance(e, gspread.exceptions.GSpreadException): # 確保不是 gspread 錯誤
                print(f"  處理圖片時發生錯誤 (第一輪) ({url}): {e}")
                # 打印詳細錯誤
                import traceback
                traceback.print_exc()
                failed_urls.append(url) # 記錄失敗的 URL
                continue # 繼續處理下一個 URL
            else:
                # 如果是 gspread 錯誤，則向上拋出，由外層處理
                raise e 

    # --- 第二輪重試處理 --- 
    if failed_urls:
        print(f"--- 第一輪處理完成，有 {len(failed_urls)} 個 URL 處理失敗，開始第二輪重試 ---")
        print("重新從 Discord 獲取最新圖片 URL...")
        success_retry, fresh_discord_urls = get_discord_images_sync()

        if not success_retry or not fresh_discord_urls:
            print("錯誤：無法為第二輪重試獲取新的 Discord URL，放棄重試。")
        else:
            print(f"成功為第二輪重試獲取了 {len(fresh_discord_urls)} 個新 URL")
            
            # 創建新 URL 的查找字典 (檔名 -> 新 URL)
            fresh_url_map = {}
            for fresh_url in fresh_discord_urls:
                try:
                    base_filename = fresh_url.split('/')[-1].split('?')[0]
                    filename = base_filename.removeprefix("CountryState_").removesuffix(".png")
                    fresh_url_map[filename] = fresh_url
                except Exception as e:
                    print(f"解析新獲取的 URL 時出錯 {fresh_url}: {e}")
            
            print(f"開始處理 {len(failed_urls)} 個之前失敗的 URL (第二輪)... ")
            # 遍歷之前失敗的 URL
            for old_failed_url in failed_urls:
                 try:
                    old_base_filename = old_failed_url.split('/')[-1].split('?')[0]
                    old_filename = old_base_filename.removeprefix("CountryState_").removesuffix(".png")
                    
                    # 查找對應的新 URL
                    new_url_to_retry = fresh_url_map.get(old_filename)
                    
                    if not new_url_to_retry:
                        print(f"  未能在新獲取的列表中找到 {old_filename} 的對應 URL，跳過重試。")
                        continue

                    print(f"--- 正在重試處理 (第二輪): {old_filename} 使用新 URL ---")
                    # print(f"   舊URL: {old_failed_url}") # 可選：打印舊 URL 以供對比
                    # print(f"   新URL: {new_url_to_retry}") # 可選：打印新 URL

                    # --- 在這裡複製第一輪的處理邏輯，但不再記錄失敗 --- 
                    response = requests.get(new_url_to_retry, timeout=15)
                    response.raise_for_status()

                    img = Image.open(BytesIO(response.content))
                    processed_img = preprocess_image(img)

                    properties = getAllProperties(processed_img)
                    print(f"  提取結果 (第二輪): {properties}")

                    timestamp = get_current_utc8_time_str() # 使用 UTC+8 時間
                    row_data = [
                        old_filename, # 使用原始檔名
                        properties.get("Military", ""),
                        properties.get("Trade", ""),
                        properties.get("Tech", ""),
                        properties.get("Culture", ""),
                        timestamp
                    ]

                    worksheet.append_row(row_data, value_input_option='USER_ENTERED')
                    print(f"  數據已寫入 Google Sheet (第二輪): {row_data}")
                    print("-----------------------------------")
                    time.sleep(1.5)

                 except requests.exceptions.RequestException as e:
                    print(f"  下載圖片時發生錯誤 (第二輪) {new_url_to_retry}: {e}")
                    # 第二輪不再重試，直接繼續下一個
                    continue 
                 except Exception as e:
                    if not isinstance(e, gspread.exceptions.GSpreadException):
                         print(f"  處理圖片時發生錯誤 (第二輪) ({new_url_to_retry}): {e}")
                         import traceback
                         traceback.print_exc()
                         # 第二輪不再重試，直接繼續下一個
                         continue
                    else:
                        raise e # 向上拋出 gspread 錯誤
            print("--- 第二輪重試處理結束 ---")
            
    else:
        print("--- 第一輪處理完成，所有 URL 均成功處理 --- ")

if __name__ == "__main__":
    main()
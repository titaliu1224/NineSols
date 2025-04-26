import asyncio
import datetime
import os
import re
import sys  # 引入 sys 模組用於 stdout flush

import discord
# from apscheduler.schedulers.asyncio import AsyncIOScheduler # 移除排程器導入
from dotenv import load_dotenv  # 引入 load_dotenv

load_dotenv()

# 調試日誌開關
DEBUG_LOGS = True

def log(message):
    """日誌函數，只有在 DEBUG_LOGS 為 True 時才輸出"""
    if DEBUG_LOGS:
        print(f"[DEBUG] {message}")
        sys.stdout.flush()  # 確保立即輸出，不緩衝

USER_TOKEN = os.getenv('DISCORD_USER_TOKEN', 'DEFAULT_TOKEN')
CHANNEL_ID = 1362649898977333360 

# discord.py-self 不使用 Intents
# intents = discord.Intents.default()
# intents.message_content = True

state_name = {
 "CountryState_Yiguo.png": "夷國",
 "CountryState_Changuo.png": "闡國",
 "CountryState_Yumin.png": "羽民國",
 "CountryState_Xiaguo.png": "夏國",
 "CountryState_Ying.png": "瀛國",
 "CountryState_Yan.png": "奄國",
 "CountryState_Shang.png": "商國",
 "CountryState_GuiFang.png": "鬼方國"
}

# --- 移除全局 URL 緩存 ---
# COLLECTED_IMAGE_URLS = []

# --- 移除不再需要的佔位符函數 ---
# def collect_image_url(url: str):
#     ...
# download_image = collect_image_url

# def get_state_status(state: str):
#     ...

# def check_and_insert_state_data(state_data: dict):
#     ...
# --- 移除佔位符函數結束 ---


# --- 整合的 MyClient 類別 ---
class MyClient(discord.Client):
    def __init__(self):
        # discord.py-self 不需要 intents 參數
        log("初始化 Discord 客戶端...")
        super().__init__()
        # self.scheduler = AsyncIOScheduler() # 移除排程器初始化
        # self.collected_urls = []  # 這個似乎是累積的，我們需要最近一次運行的
        self.last_run_urls = [] # 用於存儲最近一次 read_state_status 收集到的 URL

    async def on_ready(self):
        log(f"Discord 客戶端已登入 - {self.user.name} ({self.user.id})")
        try:
            # 首次立即執行
            log("on_ready: 開始執行 read_state_status()...")
            await self.read_state_status()
            log(f"on_ready: read_state_status() 完成，收集到 {len(self.last_run_urls)} 個 URL")
        except Exception as e:
            print(f"on_ready: 執行 read_state_status 時發生錯誤: {e}")
        finally:
            # 無論成功或失敗，在完成任務後關閉客戶端
            log("on_ready: 任務完成，準備關閉客戶端...")
            await self.close()
            log("on_ready: 客戶端已關閉")

    async def close(self):
        """確保在關閉時停止排程器"""
        log("正在關閉 Discord 客戶端...")
        # --- 移除排程相關代碼 ---
        # if self.scheduler.running:
        #     self.scheduler.shutdown()
        # --- 移除排程相關代碼結束 ---
        # 添加 try-except 以防關閉過程中出錯
        try:
            await super().close()
            log("Discord 客戶端已成功關閉")
        except Exception as e:
            print(f"關閉客戶端時發生錯誤: {e}")

    async def read_state_status(self):
        log("開始讀取狀態...")
        # 清空上次運行的結果
        self.last_run_urls = []
        channel = self.get_channel(CHANNEL_ID) 

        if not channel:
            print(f"錯誤：在 read_state_status 中找不到頻道 ID: {CHANNEL_ID}")
            # 嘗試 fetch (但如果在 on_ready 之前 client 未完全就緒，可能仍失敗)
            try:
                log("嘗試 fetch 頻道...")
                channel = await self.fetch_channel(CHANNEL_ID)
                log(f"成功獲取頻道: {channel.name}")
            except discord.NotFound:
                print(f"錯誤：透過 fetch 也找不到 ID 為 {CHANNEL_ID} 的頻道。")
                return # 無法繼續
            except discord.Forbidden:
                print(f"錯誤：沒有權限存取 ID 為 {CHANNEL_ID} 的頻道。")
                return # 無法繼續
            except Exception as e:
                print(f"嘗試 fetch 頻道時發生錯誤：{e}")
                return # 無法繼續
        
        if not channel:
             print(f"錯誤：最終未能獲取頻道 {CHANNEL_ID}，無法讀取狀態。")
             return

        # state_list = [] # 似乎也不需要了，因為只收集 URL
        # image_urls_collected = [] # 不再需要本地變數，使用 self.last_run_urls
        try:
            # 注意這裡的 limit=10，與您提供的程式碼一致
            # 如果要抓取更多歷史，需要調整 limit，但風險隨之增加
            log(f"開始從頻道 {channel.name} 抓取最近 10 條訊息...")
            message_count = 0
            async for message in channel.history(limit=10):
                message_count += 1
                log(f"處理第 {message_count} 條訊息 (ID: {message.id})...")
                if message.attachments:
                    try:
                        url = message.attachments[0].url
                        # 從 URL 提取檔名部分
                        filename = url.split("/")[-1].split("?")[0]
                        log(f"發現附件: {filename}")
                        if filename in state_name:
                            state = state_name[filename]
                            log(f"識別為有效國家圖片: {state}")
                            # --- 移除對 collect_image_url 的調用 ---
                            # collect_image_url(url)
                            # --- 移除對 collect_image_url 的調用結束 ---
                            # state_list.append(state) # 不再需要 state 列表
                            # 添加到當前運行的 URL 列表
                            if url not in self.last_run_urls:
                                self.last_run_urls.append(url)
                                log(f"添加到本次運行列表，當前共 {len(self.last_run_urls)} 個URL")
                            else:
                                log(f"URL 已存在於本次運行列表中，跳過")
                        else:
                            # 僅在調試模式下輸出此信息，避免干擾
                            log(f"  訊息 {message.id} 的附件檔名 {filename} 未在 state_name 中定義。")
                    except IndexError:
                         print(f"  訊息 {message.id} 的 attachments 列表為空。")
                    except KeyError:
                         # 如果 split 後的檔名不在 state_name 中
                         filename_from_url = url.split("/")[-1].split("?")[0]
                         print(f"  錯誤：檔名 '{filename_from_url}' 不在 state_name 字典中。URL: {url}")
                    except Exception as e:
                         print(f"  處理訊息 {message.id} 附件時發生錯誤: {e}")

            log(f"訊息處理完成，共處理 {message_count} 條訊息，找到 {len(self.last_run_urls)} 個有效國家圖片URL")
            if not self.last_run_urls: # 檢查是否有收集到 URL
                print("在此次抓取的訊息中未找到符合條件的 state 圖片 URL。")
                return

            # --- 移除不再需要的後續處理 ---
            # # 這裡實際上我們只需要 URL，不需要處理圖片內容
            # # 保留這段代碼只為了不破壞原有流程
            # if not DEBUG_LOGS:
            #     # 在非調試模式下，直接跳過圖片處理步驟
            #     log("非調試模式，跳過圖片處理步驟，直接返回收集到的 URL")
            #     return
            #     
            # unique_states = set(state_list) # 處理每個 state 一次
            # log(f"處理 {len(unique_states)} 個不同的國家狀態")
            # for state in unique_states:
            #     try:
            #         log(f"處理國家: {state}")
            #         state_data = get_state_status(state) # 獲取狀態數據 (使用佔位符)
            #         check_and_insert_state_data(state_data) # 檢查並插入數據 (使用佔位符)
            #     except Exception as e:
            #         print(f"處理 state '{state}' 時發生錯誤: {e}")
            # 
            # log("所有國家狀態處理完成")
            # --- 移除不再需要的後續處理結束 ---
            log("read_state_status 完成 URL 收集。")
        except discord.Forbidden:
             print(f"錯誤：沒有權限讀取頻道 #{channel.name} 的歷史訊息。")
        except Exception as e:
             print(f"在 read_state_status 處理訊息時發生未預期錯誤: {e}")
# --- MyClient 類別結束 ---


# --- 驗證 Token 格式 ---
def validate_token(token):
    """驗證 Discord token 的基本格式"""
    log("驗證 Discord token...")
    if not token or token == 'DEFAULT_TOKEN':
        return False, "Token 未設定或為預設值"
    
    # Discord token 通常是由三部分組成，用句點分隔
    # 每部分都應該是 Base64 編碼
    if not re.match(r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$', token):
        return False, "Token 格式不正確，應為三個部分組成，以句點分隔"
    
    log("Token 格式驗證通過")
    return True, "Token 格式正確"


# --- 提供給 main.py 調用的函數 ---
async def fetch_images_from_discord():
    """供 main.py 調用的函數，用於獲取 Discord 頻道中的圖片 URL。
    
    返回:
        list: 一個包含最近一次運行收集到的圖片 URL 的列表
    """
    log("開始從 Discord 獲取圖片 URL...")
    
    # 驗證 Token
    is_valid, validation_message = validate_token(USER_TOKEN)
    if not is_valid:
        print(f"TOKEN 錯誤: {validation_message}")
        print("請在 .env 文件中設置有效的 DISCORD_USER_TOKEN")
        return []

    client = MyClient()
    returned_urls = []  # 創建一個本地變數來存儲最終要返回的 URL
    
    try:
        # 啟動客戶端並等待它獲取頻道和執行 read_state_status
        log("啟動 Discord 客戶端... (這可能需要一些時間)")
        # client.start 會運行直到 on_ready 完成
        await client.start(USER_TOKEN)
        
        # 獲取最近一次運行收集到的 URL
        returned_urls = client.last_run_urls.copy()
        log(f"獲取了 {len(returned_urls)} 個最近運行的 URL")
        
        # 為了診斷，列出所有收集到的 URL
        for i, url in enumerate(returned_urls, 1):
            log(f"  URL {i}: {url}")
    except Exception as e:
        print(f"啟動或運行 Discord 客戶端時發生錯誤: {e}")
        return []
    finally:
        # 確保客戶端被正確關閉
        # 注意：client.close() 在 on_ready 中被調用了，這裡不需要再次調用，
        # 但保留 finally 結構以備將來可能的清理操作
        log("fetch_images_from_discord 的 finally 塊執行")
        # if not client.is_closed():
        #     try:
        #         log("調用 client.close()...")
        #         await client.close()
        #         log("client.close() 已完成")
        #     except Exception as e:
        #         print(f"關閉 Discord 客戶端時發生錯誤: {e}")
        
        # 確保所有未完成的任務都被取消
        try:
            log("檢查未完成的任務...")
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            if tasks:
                log(f"發現 {len(tasks)} 個待處理的任務，嘗試取消...")
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                log("所有待處理任務已取消")
            else:
                log("沒有發現待處理的任務")
        except Exception as e:
            print(f"取消任務時發生錯誤: {e}")
    
    # 返回最近一次運行收集到的 URL
    log(f"從 Discord 獲取完成，返回 {len(returned_urls)} 個最近運行的 URL")
    return returned_urls


# --- 簡化版本的 main 函數，只用於獲取圖片 URL ---
async def get_discord_images():
    """簡化版本的 main 函數，只用於獲取圖片 URL，不執行排程任務"""
    log("執行 get_discord_images()...")
    
    log("調用 fetch_images_from_discord()...")
    start_time = datetime.datetime.now()
    urls = await fetch_images_from_discord()
    end_time = datetime.datetime.now()
    log(f"fetch_images_from_discord() 完成，耗時: {(end_time-start_time).total_seconds()}秒")
    
    log(f"get_discord_images() 完成，返回 {len(urls)} 個 URL")
    return urls


# --- 供外部調用的同步函數 ---
def get_discord_images_sync():
    """供外部調用的同步函數，用於獲取 Discord 頻道中的圖片 URL
    
    返回:
        tuple: (成功狀態, list) - (成功狀態表示是否成功連接 Discord 並獲取數據, URLs列表)
    """
    log("開始執行 get_discord_images_sync()...")
    try:
        log("調用 asyncio.run() 執行異步函數...")
        start_time = datetime.datetime.now()
        
        # 設置超時時間，防止永久阻塞
        urls = asyncio.run(asyncio.wait_for(get_discord_images(), timeout=60.0))
        
        end_time = datetime.datetime.now()
        log(f"異步函數執行完成，耗時: {(end_time-start_time).total_seconds()}秒")
        
        if urls:
            log(f"成功獲取 {len(urls)} 個 URL")
            return True, urls
        else:
            print("從 Discord 獲取圖片 URL 失敗：未找到符合條件的圖片")
            return False, []
    except asyncio.TimeoutError:
        print("從 Discord 獲取圖片 URL 超時（執行超過60秒）")
        return False, []
    except Exception as e:
        print(f"從 Discord 獲取圖片 URL 時發生錯誤: {e}")
        import traceback
        traceback.print_exc()  # 打印詳細的錯誤棧
        return False, []


# --- 移除不再需要的 get_country_image_urls ---
# def get_country_image_urls():
#     ...


if __name__ == "__main__":
    # 需要安裝: pip install -U discord.py-self python-dotenv requests
    # 這個區塊只用於直接運行 selfBotExecutor.py 進行測試
    # 不會被 main.py 調用
    print("直接運行 selfBotExecutor.py 進行測試...")
    success, urls = get_discord_images_sync()
    if success:
        print(f"測試成功，獲取到 {len(urls)} 個 URL:")
        for i, url in enumerate(urls, 1):
            print(f"  {i}: {url}")
    else:
        print("測試失敗")
    print("測試運行結束。") 
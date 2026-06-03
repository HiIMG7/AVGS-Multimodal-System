import json
import os
import requests
import time
import sys
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
except ImportError:
    print("[Error] 找不到 moviepy，請先執行 pip install moviepy")
    sys.exit(0)

print("=== 動態虛擬人引擎 (D-ID) 全自動單次生成與切割模組 ===")

current_dir = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(current_dir, "config.json")
JSON_PATH = os.path.join(current_dir, "avgs_data.json")
AUDIO_DIR = os.path.join(current_dir, "temp_audio_clips")
AVATAR_DIR = os.path.join(current_dir, "temp_avatar_clips")
AVATAR_IMG = os.path.join(current_dir, "avatar.png")

COMBINED_AUDIO = os.path.join(current_dir, "combined_audio.mp3")
COMBINED_VIDEO = os.path.join(current_dir, "combined_avatar.mp4")

if not os.path.exists(AVATAR_DIR):
    os.makedirs(AVATAR_DIR)

# --- 讀取設定與檢查 ---
try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    DID_KEY = config.get("did_key")
except Exception:
    DID_KEY = None

if not DID_KEY:
    print("[Warning] 找不到 D-ID API Key，將跳過動態主播生成。")
    sys.exit(0)

if not os.path.exists(AVATAR_IMG):
    print(f"[Warning] 找不到虛擬主播圖片: {AVATAR_IMG}，將跳過動態生成。")
    sys.exit(0)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    slides_data = json.load(f)
    


print("\n--- 1. 開始處理與合併音檔 ---")
audio_clips = []
durations = []

for i in range(len(slides_data)):
    audio_path = os.path.join(AUDIO_DIR, f"audio_{i:02d}.mp3")
    if not os.path.exists(audio_path):
        print(f"[Warning] 找不到音檔 {audio_path}，跳過動態生成。")
        sys.exit(0)
    
    clip = AudioFileClip(audio_path)
    audio_clips.append(clip)
    durations.append(clip.duration)
    print(f"  載入 audio_{i:02d}.mp3 (長度: {clip.duration:.2f} 秒)")

print("  正在匯出合併音檔 combined_audio.mp3...")
final_audio = concatenate_audioclips(audio_clips)
final_audio.write_audiofile(COMBINED_AUDIO, logger=None)

for clip in audio_clips: clip.close()
final_audio.close()

headers = {"Authorization": f"Basic {DID_KEY}", "accept": "application/json"}

print("\n--- 2. 正在上傳素材至 D-ID ---")
with open(AVATAR_IMG, "rb") as img_file:
    resp = requests.post("https://api.d-id.com/images", headers=headers, files={"image": ("avatar.png", img_file, "image/png")})
    if resp.status_code != 201:
        print(f"[Warning] 頭像上傳失敗: {resp.text}，跳過動態生成。")
        sys.exit(0)
    source_url = resp.json()["url"]

with open(COMBINED_AUDIO, "rb") as aud_file:
    a_resp = requests.post("https://api.d-id.com/audios", headers=headers, files={"audio": ("combined_audio.mp3", aud_file, "audio/mpeg")})
    if a_resp.status_code != 201:
        print(f"[Warning] 音檔上傳失敗: {a_resp.text}，跳過動態生成。")
        sys.exit(0)
    audio_url = a_resp.json()["url"]

print("\n--- 3. 請求生成動態長影片 ---")
talk_data = {
    "source_url": source_url,
    "script": {"type": "audio", "audio_url": audio_url},
    "config": {"transparent_background": True}
}
post_headers = {"Authorization": f"Basic {DID_KEY}", "accept": "application/json", "content-type": "application/json"}
t_resp = requests.post("https://api.d-id.com/talks", headers=post_headers, json=talk_data)

if t_resp.status_code != 201:
    print(f"[Warning] 動態生成請求失敗 (可能是 Token 不足): {t_resp.text}")
    print("將略過動態生成，保留純簡報輸出。")
    sys.exit(0)
    
talk_id = t_resp.json()["id"]

print("\n--- 4. 等待雲端渲染完成 ---")
result_url = None
while True:
    time.sleep(5)
    s_resp = requests.get(f"https://api.d-id.com/talks/{talk_id}", headers=headers)
    status = s_resp.json().get("status")
    print(f"  狀態檢查: {status}...")
    
    if status == "done":
        result_url = s_resp.json()["result_url"]
        break
    elif status == "error":
        print(f"[Warning] 雲端渲染發生錯誤，跳過動態生成。")
        sys.exit(0)

print("\n--- 5. 正在下載生成的長影片 ---")
v_resp = requests.get(result_url)
with open(COMBINED_VIDEO, "wb") as f:
    f.write(v_resp.content)
print(f"  [OK] 長影片已儲存: {COMBINED_VIDEO}")


print("\n--- 6. 開始根據時長進行自動切割 ---")
video = VideoFileClip(COMBINED_VIDEO)
current_start_time = 0.0

for i, duration in enumerate(durations):
    end_time = current_start_time + duration
    if end_time > video.duration: end_time = video.duration
        
    out_path = os.path.join(AVATAR_DIR, f"avatar_{i:02d}.mp4")
    print(f"  擷取 Slide {i:02d} ({current_start_time:.2f}s - {end_time:.2f}s) -> {out_path}")
    
    clip = video.subclip(current_start_time, end_time)
    clip.write_videofile(out_path, codec="libx264", audio_codec="aac", logger=None)
    current_start_time = end_time

video.close()

if os.path.exists(COMBINED_AUDIO): os.remove(COMBINED_AUDIO)
if os.path.exists(COMBINED_VIDEO): os.remove(COMBINED_VIDEO)

print("\n========================================")
print(" 所有動態虛擬人生成與切割完畢！")
print("========================================")
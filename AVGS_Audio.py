import json
import os
import requests

print("Audio模型開始運作")

# 1. 設定 API Key
current_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(current_dir, "config.json"), "r") as f:
    config = json.load(f)

XI_API_KEY = config["elevenlabs_key"]
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"

# 2. 設定絕對路徑 (鎖定在程式同一資料夾)
current_dir = os.path.dirname(os.path.abspath(__file__))

# 輸入：JSON 檔案路徑
JSON_PATH = os.path.join(current_dir, "avgs_data.json")

# 輸出：音訊資料夾路徑
AUDIO_DIR = os.path.join(current_dir, "temp_audio_clips")

# 檢查 JSON 是否存在
if not os.path.exists(JSON_PATH):
    print(f"[Error] 找不到 JSON 檔案: {JSON_PATH}")
    print("請先執行 AVGS_Gemini.py 生成資料！")
    exit()

# 建立存放音訊的資料夾
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)
    print(f"--- Created Audio Directory: {AUDIO_DIR} ---")

def generate_clip(text, index):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = { "xi-api-key": XI_API_KEY, "Content-Type": "application/json" }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            filename = f"audio_{index:02d}.mp3"
            # 使用絕對路徑存檔
            path = os.path.join(AUDIO_DIR, filename)
            
            with open(path, "wb") as f:
                f.write(response.content)
            print(f"  [OK] Clip {index} saved to: {path}")
            return path
        else:
            print(f"  [Error] Clip {index} failed. Status: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"  [Error] Connection failed: {e}")
        return None

# --- 主程式 ---
try:
    # 讀取 JSON
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        slides_data = json.load(f)

    print(f"--- Generating {len(slides_data)} audio clips... ---")

    for i, slide in enumerate(slides_data):
        script = slide.get('script', '')
        if script:
            print(f"Processing Slide {i+1}...")
            generate_clip(script, i)
        else:
            print(f"Processing Slide {i+1}... [Skipped] No script found.")

    print("="*40)
    print("All audio clips generated.")
    print(f"Folder: {AUDIO_DIR}")
    print("="*40)

except Exception as e:
    print(f"[Critical Error] {e}")
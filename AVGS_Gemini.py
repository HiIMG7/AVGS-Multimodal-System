import json
import os
import re
from google import genai

print("文本解析與大腦模組開始運作")


current_dir = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON = os.path.join(current_dir, "avgs_data.json")
CONFIG_FILE = os.path.join(current_dir, "config.json")
PROMPT_FILE = os.path.join(current_dir, "prompt.txt")

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    MY_API_KEY = config["gemini_key"]
except Exception as e:
    print(f"[錯誤] 無法讀取 config.json，請確認金鑰設定是否正確。({e})")
    exit()

VALID_INPUTS = ["paper.pdf", "paper.png", "paper.jpg", "paper.jpeg"]
input_path = None

for filename in VALID_INPUTS:
    temp_path = os.path.join(current_dir, filename)
    if os.path.exists(temp_path):
        input_path = temp_path
        break

if not input_path:
    print(f"[錯誤] 找不到輸入檔案，請確認資料夾內是否有 {VALID_INPUTS} 其中一種格式。")
    exit()

print(f"偵測到輸入檔案: {os.path.basename(input_path)}")


DEFAULT_PROMPT = """你是一個專業的知識傳播與影音製作人。請閱讀這份上傳的檔案，並規劃一份 4 頁的簡報影音腳本。
這份檔案可能是「學術論文」、「財經新聞」、「商業報告」或「一般教學講義」。

【最高指導原則】：
你必須「只」回傳一個純 JSON 格式的陣列（List of Objects）。絕對不要加上任何 Markdown 標記（如 ```json）或前後廢話。你的輸出必須能直接被 Python 讀取。
【語言強制要求】：
"title" 與 "points" 的內容必須使用「英文 (English)」。
"script" 主播講稿的內容必須使用「繁體中文 (Traditional Chinese)」。

* 第一頁 (封面頁 Index 0)：
- "title": 擷取檔案的完整大標題 (English)。
- "points": 包含 3 個字串的陣列：1. "Source: [來源]" 2. "[年份], Published by [單位]" 3. "Author: [作者]"。(若找不到請填寫 "N/A"，English)
- "script": 虛擬主播的開場歡迎詞（約 40-50 字，繁體中文）。語氣專業。

* 第二頁至第四頁 (內容頁 Index 1~3)：
- "title": 該頁的核心論點標題 (English)。
- "points": 該頁 3 個重點（每點精簡在 15 字以內的「高濃度關鍵字」，English）。
- "script": 對應的主播講稿（約 50-60 字，繁體中文）。必須是對 points 的「白話文擴充解釋」，加入自然的口語轉折，絕對不可單純朗讀字卡。
"""

if os.path.exists(PROMPT_FILE):
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
            if not prompt:
                prompt = DEFAULT_PROMPT
            else:
                print("已載入使用者自訂的 Prompt！")
    except:
        prompt = DEFAULT_PROMPT
else:
    prompt = DEFAULT_PROMPT
    print("使用系統預設的 Prompt 範例進行解析。")

def clean_json(text):
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()

client = genai.Client(api_key=MY_API_KEY)

try:
    print("正在上傳檔案至 Gemini 視覺引擎...")
    uploaded_file = client.files.upload(file=input_path)
    print("檔案上傳成功。")
    
    print("正在要求 Gemini 解析內容與生成腳本...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[uploaded_file, prompt]
    )

    json_str = clean_json(response.text)
    data = json.loads(json_str)
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("========================================")
    print("SUCCESS! 結構化腳本已儲存至:")
    print(OUTPUT_JSON)
    print("========================================")
    
except json.JSONDecodeError:
    print("[錯誤] 模型回傳的不是正確的 JSON 格式。")
    print("回傳內容：\n", response.text)
except Exception as e:
    print(f"[錯誤] 系統執行失敗: {e}")
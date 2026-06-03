import streamlit as st
import os
import subprocess
import json
import time
import re

# 初始化 Session State
if 'api_time' not in st.session_state:
    st.session_state.api_time = 0.0

st.set_page_config(page_title="AVGS 智能影音生成系統", layout="wide", page_icon="🎬")
current_dir = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(current_dir, "avgs_data.json")
OUTPUT_VIDEO = os.path.join(current_dir, "AVGS_Final_Output.mp4")
CONFIG_FILE = os.path.join(current_dir, "config.json")
PROMPT_FILE = os.path.join(current_dir, "prompt.txt")

with st.sidebar:
    st.header("⚙️ 系統控制台")
    st.divider()

    st.subheader("🔄 運作模式切換")
    work_mode = st.radio("選擇系統執行流程：", [
        "🛠️ 人機協作模式 (自訂 Prompt / 修改講稿)", 
        "⚡ 一條龍模式 (跳過人工修改，極速直出)"
    ], label_visibility="collapsed")
    st.divider()

    st.subheader("🚀 渲染引擎選擇")
    engine_mode = st.radio("選擇影音縫合核心：", [
        "🏎️ 渦輪極速模式 (FFmpeg 底層引擎，推薦)",
        "🐢 穩定相容模式 (MoviePy 原生引擎)"
    ], label_visibility="collapsed")
    st.divider()

    st.subheader("🔑 API 金鑰綁定")
    default_gemini, default_eleven, default_did = "", "", ""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
                default_gemini = cfg.get("gemini_key", "")
                default_eleven = cfg.get("elevenlabs_key", "")
                default_did = cfg.get("did_key", "")
        except: pass
    
    gemini_key = st.text_input("Gemini API Key", value=default_gemini, type="password")
    eleven_key = st.text_input("ElevenLabs API Key", value=default_eleven, type="password")
    did_key = st.text_input("D-ID API Key", value=default_did, type="password")
    
    if st.button("💾 儲存金鑰", use_container_width=True):
        new_cfg = {"gemini_key": gemini_key, "elevenlabs_key": eleven_key, "did_key": did_key, "voice_id": "nPczCjzI2devNBz1zQrb"}
        with open(CONFIG_FILE, "w") as f: json.dump(new_cfg, f, indent=2)
        st.success("金鑰已寫入系統！")
    st.divider()

    st.subheader("🖼️ 視覺素材庫")
    bg_title_file = st.file_uploader("更換封面背景", type=["png", "jpg"])
    if bg_title_file:
        with open(os.path.join(current_dir, "bg_title.png"), "wb") as f: f.write(bg_title_file.getbuffer())
        
    bg_content_file = st.file_uploader("更換內頁背景", type=["png", "jpg"])
    if bg_content_file:
        with open(os.path.join(current_dir, "bg_content.png"), "wb") as f: f.write(bg_content_file.getbuffer())
        
    avatar_file = st.file_uploader("更換虛擬主播", type=["png"])
    if avatar_file:
        with open(os.path.join(current_dir, "avatar.png"), "wb") as f: f.write(avatar_file.getbuffer())

def run_smooth_pipeline(total_slides):
    progress_bar = st.progress(0)
    status_text = st.empty()
    current_progress = [0.0] 

    def smooth_update(target_pct, message):
        status_text.text(f"⏳ {message}")
        while current_progress[0] < target_pct:
            current_progress[0] += 0.5 
            if current_progress[0] > 100: current_progress[0] = 100
            progress_bar.progress(int(current_progress[0]))
            time.sleep(0.01) 
        current_progress[0] = target_pct
        progress_bar.progress(int(current_progress[0]))

    def run_script_with_progress(script_name, start_pct, end_pct, stage_name):
        process = subprocess.Popen(
            ["python", script_name], cwd=current_dir, stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace"
        )
        step_per_slide = (end_pct - start_pct) / max(total_slides, 1)
        slides_done = 0
        error_log = [] 

        for line in process.stdout:
            line = line.strip()
            if not line: continue
            error_log.append(line)
            
            if "now=None" in line or "%|" in line or "it/s" in line:
                match = re.search(r'(\d+)\s*%.*?\[(\d+:\d+)<(\d+:\d+)', line)
                if match:
                    pct, elapsed, eta = match.groups()
                    action = "🎵 音訊處理中" if "chunk" in line or "snd" in line else "🎞️ 影像渲染中"
                    clean_msg = f"{action} | 進度: {pct}% | 已耗時: {elapsed} | 預估剩餘: {eta}"
                    status_text.text(f"⏳ {stage_name} | {clean_msg}")
                    
                    if "Movie" in script_name and "Turbo" not in script_name:
                        real_pct = min(100, int(start_pct + (int(pct) / 100.0 * (end_pct - start_pct))))
                        progress_bar.progress(real_pct)
                        current_progress[0] = real_pct
                else:
                    pct_match = re.search(r'(\d+)\s*%', line)
                    if pct_match:
                        pct = pct_match.group(1)
                        status_text.text(f"⏳ {stage_name} | 進度: {pct}%")
                continue 

            if any(keyword in line.lower() for keyword in ["[ok]", "完成", "[+]", "saved"]):
                slides_done += 1
                target = start_pct + (step_per_slide * slides_done)
                if target > end_pct: target = end_pct
                smooth_update(target, f"{stage_name} | {line}")
            elif "⏱️" in line or "⚡" in line or "🔗" in line:
                status_text.text(f"🚀 {stage_name} | {line}")
            else:
                status_text.text(f"⏳ {stage_name} | {line}")
                
        process.wait()
        if process.returncode != 0:
            last_errors = "\n".join(error_log[-5:])
            st.error(f"❌ 【{script_name}】 執行失敗！最後的系統訊息：\n{last_errors}")
            raise Exception(f"{script_name} 發生錯誤")
            
        smooth_update(end_pct, f"{stage_name} | 階段完成")

    try:
        run_script_with_progress("AVGS_Audio.py", 0, 25, "語音生成 (1/4)")
        run_script_with_progress("AVGS_Vision.py", 25, 50, "視覺排版 (2/4)")
        run_script_with_progress("AVGS_Avatar.py", 50, 75, "虛擬主播 (3/4)")
        
        if "渦輪" in engine_mode:
            run_script_with_progress("AVGS_Movie_Turbo.py", 75, 100, "渦輪極速影音縫合 (4/4)")
        else:
            run_script_with_progress("AVGS_Movie.py", 75, 100, "穩定相容影音縫合 (4/4)")
            
        status_text.success("✅ 渲染管線執行完畢！")
        return True
    except Exception as e:
        st.error(f"系統渲染中斷。詳細原因：{e}")
        return False

st.title("🚀 AVGS: 智能影音生成系統")

if "一條龍" in work_mode: 
    st.markdown("⚡ **一條龍模式**：上傳檔案後一鍵直達出片。")
else: 
    st.markdown("🛠️ **人機協作模式**：系統將提供腳本草稿，供您審閱與微調。")
st.divider()

st.header("1️⃣ 上傳原始文檔")
uploaded_file = st.file_uploader("支援 PDF 論文、PNG/JPG 圖片截圖", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    file_ext = uploaded_file.name.split('.')[-1]
    save_path = os.path.join(current_dir, f"paper.{file_ext}")
    with open(save_path, "wb") as f: f.write(uploaded_file.getbuffer())
    st.success(f"檔案暫存成功：paper.{file_ext}")

    if "人機協作" in work_mode:
        st.header("2️⃣ 選擇解析情境 (Prompt Template)")
        
        prompt_templates = {
            "🎓 學術論文解說": """你是一個專業的學術影音製作人。請閱讀這份學術論文，並規劃一份 4 頁的簡報影音腳本。
【最高指導原則】：你必須「只」回傳一個純 JSON 格式的陣列 (List of Objects)，絕對不要加上任何 Markdown 標記或廢話。
【語言強制要求】："title" 與 "points" 必須使用「英文 (English)」撰寫。"script" 必須使用「繁體中文 (Traditional Chinese)」撰寫。
* 封面頁 (Index 0)：
- "title": 論文大標題 (English)。
- "points": 包含 3 個字串：1. "Journal: [期刊]" 2. "[年份], Published by [出版社]" 3. "Country: [國家]"。(若截圖中找不到，請填寫 "N/A"，English)
- "script": 專業的開場歡迎詞 (約40-50字，繁體中文)。
* 內容頁 (Index 1~3)：
- "title": 該頁核心論點 (English)。
- "points": 該頁 3 個重點 (每點精簡在 15 字以內的「高濃度關鍵字」，English)。
- "script": 對應的主播講稿 (約50-60字，繁體中文)，需以口語化解釋 points，加入口語轉折詞，絕對不可單純朗讀字卡。""",
            
            "💼 商業企劃簡報": """你是一個充滿說服力的商業簡報專家。請閱讀這份商業文件，並規劃一份 4 頁的簡報影音腳本。
【最高指導原則】：你必須「只」回傳一個純 JSON 格式的陣列 (List of Objects)，絕對不要加上任何 Markdown 標記或廢話。
【語言強制要求】："title" 與 "points" 必須使用「英文 (English)」撰寫。"script" 必須使用「繁體中文 (Traditional Chinese)」撰寫。
* 封面頁 (Index 0)：
- "title": 企劃大標題 (English)。
- "points": 包含 3 個字串：1. "Source: [來源/公司]" 2. "[年份], Published by [單位]" 3. "Region: [地區]"。(若截圖中找不到，請填寫 "N/A"，English)
- "script": 自信且具吸引力的開場白 (約40-50字，繁體中文)。
* 內容頁 (Index 1~3)：
- "title": 該頁核心論點 (English)。
- "points": 該頁 3 個重點 (每點精簡在 15 字以內的「高濃度關鍵字」，English)。
- "script": 具備商業說服力的講稿 (約50-60字，繁體中文)，需強調效益與價值，加入口語轉折詞，絕對不可單純朗讀字卡。""",
            
            "🏫 一般教學講義": """你是一個親切的知識型 YouTuber。請閱讀這份教學講義，並規劃一份 4 頁的教學影音腳本。
【最高指導原則】：你必須「只」回傳一個純 JSON 格式的陣列 (List of Objects)，絕對不要加上任何 Markdown 標記或廢話。
【語言強制要求】："title" 與 "points" 必須使用「英文 (English)」撰寫。"script" 必須使用「繁體中文 (Traditional Chinese)」撰寫。
* 封面頁 (Index 0)：
- "title": 課程單元名稱 (English)。
- "points": 包含 3 個字串：1. "Topic: [主題分類]" 2. "Level: [難易度]" 3. "Instructor: [講師]"。(若截圖中找不到，請填寫 "N/A"，English)
- "script": 親切活潑的開場白 (約40-50字，繁體中文)。
* 內容頁 (Index 1~3)：
- "title": 該頁學習重點 (English)。
- "points": 該頁 3 個核心知識 (每點精簡在 15 字以內的「高濃度關鍵字」，English)。
- "script": 淺顯易懂的教學講稿 (約50-60字，繁體中文)，多用生活化的比喻，語氣需自然生動，絕對不可單純朗讀字卡。"""
        }
        
        selected_template = st.radio("請選擇最符合您文件的風格：", list(prompt_templates.keys()))
        
        expert_mode = st.toggle("⚙️ 開啟進階專家模式 (直接修改底層 Prompt)")
        
        if expert_mode:
            st.warning("⚠️ 警告：修改核心 JSON 結構指令可能導致系統解析崩潰，請謹慎編輯。")
            final_prompt = st.text_area("自訂 Prompt 邏輯：", value=prompt_templates[selected_template], height=300)
        else:
            final_prompt = prompt_templates[selected_template]

        if st.button("🧠 開始大腦解析 (生成腳本)", use_container_width=True):
            api_start = time.time() 
            
            with open(PROMPT_FILE, "w", encoding="utf-8") as f: f.write(final_prompt)
            with st.spinner("Gemini 正在極速閱讀與排版中，請稍候..."):
                result = subprocess.run(["python", "AVGS_Gemini.py"], cwd=current_dir, capture_output=True, text=True)
                
                if result.returncode == 0: 
                    api_end = time.time() 
                    st.session_state.api_time = api_end - api_start 
                    st.success(f"腳本生成完畢！ (大腦解析耗時: {st.session_state.api_time:.2f} 秒) 請在下方進行微調。")
                else: 
                    st.error(f"解析失敗，錯誤訊息：\n{result.stderr}")

        if os.path.exists(JSON_FILE):
            st.divider()
            st.header("3️⃣ 腳本檢閱與微調")
            
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    slides_data = json.load(f)
                    
                with st.form("script_editor_form"):
                    st.info("💡 請直接在下方修改內容。系統會在背景自動為您計算 API 消耗成本。")
                    edited_data = []
                    
                    for i, slide in enumerate(slides_data):
                        with st.expander(f"📝 投影片 {i+1}：{slide.get('title', '無標題')}", expanded=(i==0)):
                            new_title = st.text_input("📌 Title (標題 / 英文)", value=slide.get("title", ""), key=f"title_{i}")
                            
                            points_str = "\n".join(slide.get("points", []))
                            new_points_str = st.text_area("📋 Points (重點 / 英文 - 請確保每行一點)", value=points_str, height=100, key=f"points_{i}")
                            new_points = [p.strip() for p in new_points_str.split("\n") if p.strip()]
                            
                            new_script = st.text_area("🎙️ Script (主播講稿 / 中文)", value=slide.get("script", ""), height=100, key=f"script_{i}")
                            
                            edited_data.append({
                                "title": new_title,
                                "points": new_points,
                                "script": new_script
                            })
                            
                    submit_button = st.form_submit_button("🎬 確認內容無誤，啟動渲染管線", type="primary", use_container_width=True)

                if submit_button:
                    total_audio_chars = sum(len(slide["script"]) for slide in edited_data)
                    SAFE_LIMIT = 1500 
                    
                    if total_audio_chars > SAFE_LIMIT:
                        st.error(f"🛑 【系統熔斷保護啟動】\n\n您的講稿總字數為 **{total_audio_chars} 字**，已超過單次安全上限 ({SAFE_LIMIT} 字)。\n為避免 API 費用爆增與系統崩潰，請精簡您的「🎙️ Script (主播講稿)」後再試一次！")
                    else:
                        est_cost_usd = total_audio_chars * 0.0004 
                        st.info(f"💰 **資源消耗評估通過**：本次預估生成 {total_audio_chars} 個語音字元 (API 成本約 ${est_cost_usd:.3f} USD)。")
                        
                        with open(JSON_FILE, "w", encoding="utf-8") as f: 
                            json.dump(edited_data, f, ensure_ascii=False, indent=2)
                        
                        st.success("講稿安全儲存！系統開始渲染...")
                        total_slides = len(edited_data)
                        
                        render_start = time.time()
                        success = run_smooth_pipeline(total_slides)
                        render_end = time.time()
                        
                        if success:
                            render_time = render_end - render_start
                            total_system_time = st.session_state.api_time + render_time
                            
                            st.success(f"""🏆 **任務圓滿達成！系統純淨運作耗時： {total_system_time:.2f} 秒**
                            \n(已排除人工審閱時間。包含大腦解析 {st.session_state.api_time:.2f}s + 管線渲染 {render_time:.2f}s)""")
                            
            except json.JSONDecodeError:
                st.error("❌ 讀取 JSON 失敗！請重新執行步驟 2 讓系統產生正確的格式。")

    else:
        st.header("⚡ 極速產出")
        st.info("系統將在背景自動執行所有流程，請直接點擊下方按鈕。")
        if st.button("🚀 一鍵啟動：從文檔直達影片", type="primary", use_container_width=True):
            global_start = time.time() 
            
            with st.spinner("大腦運轉中：Gemini 正在進行多模態解析與腳本規劃..."):
                result = subprocess.run(["python", "AVGS_Gemini.py"], cwd=current_dir, capture_output=True, text=True)
                if result.returncode != 0:
                    st.error(f"解析失敗，流程中斷：\n{result.stderr}")
                    st.stop()
            st.success("腳本規劃完畢，無縫進入影音渲染管線！")
            
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f: total_slides = len(json.load(f))
            except: total_slides = 1
            
            success = run_smooth_pipeline(total_slides)
            
            if success:
                global_end = time.time() 
                st.success(f"🏆 **任務圓滿達成！端到端總生成耗時 (End-to-End)： {global_end - global_start:.2f} 秒**")

if os.path.exists(OUTPUT_VIDEO):
    st.divider()
    st.header("📺 最終成品展示")
    with open(OUTPUT_VIDEO, "rb") as f:
        video_bytes = f.read()
    st.video(video_bytes)
    
    st.download_button(
        label="📥 下載最終影片 (MP4)", data=video_bytes, file_name="AVGS_Final_Output.mp4",
        mime="video/mp4", type="primary"
    )
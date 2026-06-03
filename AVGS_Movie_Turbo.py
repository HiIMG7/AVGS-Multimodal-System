import os
import sys
import subprocess
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

try:
    import imageio_ffmpeg
    from moviepy.editor import AudioFileClip
except ImportError:
    print("[Error] 找不到必要套件")
    sys.exit(1)

print("🚀 終極渦輪引擎啟動 (NVIDIA RTX 硬體加速 + 精準測速版)")

current_dir = os.path.dirname(os.path.abspath(__file__))
IMG_FOLDER = os.path.join(current_dir, "temp_slides_images")
AUDIO_FOLDER = os.path.join(current_dir, "temp_audio_clips")
AVATAR_DIR = os.path.join(current_dir, "temp_avatar_clips")
OUTPUT_VIDEO = os.path.join(current_dir, "AVGS_Final_Output.mp4")
TEMP_LIST_FILE = os.path.join(current_dir, "concat_list.txt")

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

def get_files(folder, prefix, extension):
    if not os.path.exists(folder): return []
    return sorted([
        os.path.join(folder, f) for f in os.listdir(folder) 
        if f.startswith(prefix) and f.endswith(extension)
    ])

def create_final_video():
    start_time = time.time() 

    image_paths = get_files(IMG_FOLDER, "slide_", ".png")
    if not image_paths:
        print("錯誤：找不到任何簡報圖片！請確認 temp_slides_images 內有檔案。")
        return

    slide_videos = []

    for i in range(len(image_paths)):
        img = image_paths[i]
        aud = os.path.join(AUDIO_FOLDER, f"audio_{i:02d}.mp3")
        avatar_vid = os.path.join(AVATAR_DIR, f"avatar_{i:02d}.mp4")
        out_file = os.path.join(current_dir, f"temp_rendered_{i:02d}.mp4")
        
        if os.path.exists(aud):
            audio_clip = AudioFileClip(aud)
            duration = audio_clip.duration + 0.5
            audio_clip.close()
        else:
            duration = 3.0

        print(f"--- ⚡ 正在極速渲染 Slide {i:02d} ({duration:.2f}s) ---")


        cmd = [
            ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-t", str(duration), "-i", img,    
        ]
        
        has_audio = os.path.exists(aud)
        if has_audio:
            cmd.extend(["-t", str(duration), "-i", aud])     
            
        has_avatar = os.path.exists(avatar_vid)
        if has_avatar:
            cmd.extend(["-t", str(duration), "-i", avatar_vid]) 
            
        filter_complex = ""
        maps = []
        
        if has_avatar:
            audio_index = "1:a" if has_audio else None
            avatar_index = "2:v" if has_audio else "1:v"
            
            filter_complex = f"[{avatar_index}]scale=-2:280,pad=iw+8:ih+8:4:4:color=white[ava];[0:v][ava]overlay=W-w-40:H-h-40:eof_action=pass[outv]"
            maps.extend(["-map", "[outv]"])
            if has_audio: maps.extend(["-map", audio_index])
        else:
            maps.extend(["-map", "0:v"])
            if has_audio: maps.extend(["-map", "1:a"])

        if filter_complex:
            cmd.extend(["-filter_complex", filter_complex])
            
        cmd.extend(maps)
        
        cmd.extend([
            "-c:v", "h264_nvenc",  
            "-preset", "p1",        
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            out_file
        ])
        
        subprocess.run(cmd)
        slide_videos.append(out_file)
        print(f"  [+] Slide {i:02d} 完成！")

    print("\n--- 🔗 正在無縫串接所有片段 ---")
    with open(TEMP_LIST_FILE, "w", encoding="utf-8") as f:
        for vid in slide_videos:
            f.write(f"file '{vid}'\n")
            
    concat_cmd = [
        ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", TEMP_LIST_FILE,
        "-c", "copy", OUTPUT_VIDEO
    ]
    subprocess.run(concat_cmd)

    for vid in slide_videos:
        if os.path.exists(vid): os.remove(vid)
    if os.path.exists(TEMP_LIST_FILE): os.remove(TEMP_LIST_FILE)

    end_time = time.time() 
    total_elapsed = end_time - start_time 

    print(f"\n🎉 大功告成！終極渦輪版影片已產出: {OUTPUT_VIDEO}")
    print(f"⏱️ 系統真實總渲染耗時： {total_elapsed:.2f} 秒！")

if __name__ == "__main__":
    create_final_video()
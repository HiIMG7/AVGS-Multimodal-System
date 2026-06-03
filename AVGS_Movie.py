import os
import sys
try:
    from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips, CompositeVideoClip
except ImportError:
    print("[Error] 找不到 moviepy")
    sys.exit(1)

print("影片縫合模型開始運作 (完美定位 + 無回音 + 多核心極速渲染版)")

current_dir = os.path.dirname(os.path.abspath(__file__))
IMG_FOLDER = os.path.join(current_dir, "temp_slides_images")
AUDIO_FOLDER = os.path.join(current_dir, "temp_audio_clips")
AVATAR_DIR = os.path.join(current_dir, "temp_avatar_clips")
AVATAR_IMG = os.path.join(current_dir, "avatar.png") 
OUTPUT_VIDEO = os.path.join(current_dir, "AVGS_Final_Output.mp4")

def get_files(folder, prefix, extension):
    if not os.path.exists(folder): return []
    return sorted([
        os.path.join(folder, f) for f in os.listdir(folder) 
        if f.startswith(prefix) and f.endswith(extension)
    ])

def create_final_video():
    image_paths = get_files(IMG_FOLDER, "slide_", ".png")
    if not image_paths:
        print("錯誤：找不到任何簡報圖片！")
        return

    print(f"--- 開始精準同步與合成 {len(image_paths)} 個片段... ---")
    clips = []

    for i in range(len(image_paths)):
        img = image_paths[i]
        aud = os.path.join(AUDIO_FOLDER, f"audio_{i:02d}.mp3")
        avatar_vid_path = os.path.join(AVATAR_DIR, f"avatar_{i:02d}.mp4")
        
        try:
            # 1. 處理背景與語音
            if os.path.exists(aud):
                audio_clip = AudioFileClip(aud)
                duration = audio_clip.duration + 0.5 
                slide_clip = ImageClip(img).set_duration(duration).set_audio(audio_clip)
                print(f"  [+] 完成 Slide {i:02d} 背景同步 ({duration:.2f}s)")
            else:
                duration = 3.0
                slide_clip = ImageClip(img).set_duration(duration)
                print(f"  [Info] Slide {i:02d} 無語音，停留 3 秒")

            # 2. 疊加主播
            if os.path.exists(avatar_vid_path):
                print(f"      -> 疊加動態主播 (視訊方塊): avatar_{i:02d}.mp4")
                try:
                    avatar_clip = VideoFileClip(avatar_vid_path).without_audio()
                    avatar_clip = avatar_clip.resize(height=280)
                    avatar_clip = avatar_clip.margin(top=4, bottom=4, left=4, right=4, color=(255, 255, 255))
                    x_pos = 1920 - avatar_clip.w - 40
                    y_pos = 1080 - avatar_clip.h - 40
                    avatar_clip = avatar_clip.set_position((x_pos, y_pos))
                    
                    actual_v_dur = avatar_clip.duration
                    avatar_clip = avatar_clip.subclip(0, min(actual_v_dur, duration))
                        
                    slide_clip = CompositeVideoClip([slide_clip, avatar_clip]).set_duration(duration)
                except Exception as e:
                    print(f"      [Error] 動態主播疊加失敗: {e}")
            elif os.path.exists(AVATAR_IMG):
                print(f"      -> 使用靜態主播備案")
                avatar_clip = ImageClip(AVATAR_IMG).resize(height=280)
                avatar_clip = avatar_clip.margin(top=4, bottom=4, left=4, right=4, color=(255, 255, 255))
                
                x_pos = 1920 - avatar_clip.w - 40
                y_pos = 1080 - avatar_clip.h - 40
                avatar_clip = avatar_clip.set_position((x_pos, y_pos)).set_duration(duration)
                
                slide_clip = CompositeVideoClip([slide_clip, avatar_clip]).set_duration(duration)

            clips.append(slide_clip)
        except Exception as e:
            print(f"  [Skip] Slide {i:02d} 處理失敗: {e}")

    if not clips: return

    print("正在串接所有片段...")
    final_video = concatenate_videoclips(clips, method="compose")
    
    print(f"準備渲染最終影片，請稍候...")
    try:
        final_video.write_videofile(
            OUTPUT_VIDEO, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac", 
            threads=8,            
            preset="ultrafast",    
            logger="bar"           
        )
        print(f" 大功告成！影片已產出: {OUTPUT_VIDEO}")
    except Exception as e:
         print(f"存檔失敗: {e}")
         
    try:
        final_video.close()
    except:
        pass

if __name__ == "__main__":
    create_final_video()
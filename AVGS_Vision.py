import os
import json
import shutil
from PIL import Image, ImageDraw, ImageFont

print("視覺渲染引擎開始運作")

current_dir = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(current_dir, "avgs_data.json")
OUTPUT_FOLDER = os.path.join(current_dir, "temp_slides_images")
BG_TITLE = os.path.join(current_dir, "bg_title.png")
BG_CONTENT = os.path.join(current_dir, "bg_content.png")

# 字型路徑設定 (預設微軟正黑體)
FONT_PATH_BOLD = "C:\\Windows\\Fonts\\msjhbd.ttc" 
if not os.path.exists(FONT_PATH_BOLD):
    FONT_PATH_BOLD = "C:\\Windows\\Fonts\\msjh.ttc"

FONT_PATH_REG = "C:\\Windows\\Fonts\\msjh.ttc" 

def get_background(image_path, fallback_color):
    alt_path = image_path.replace(".png", ".jpg")
    if os.path.exists(image_path):
        return Image.open(image_path).convert("RGBA").resize((1920, 1080))
    elif os.path.exists(alt_path):
        return Image.open(alt_path).convert("RGBA").resize((1920, 1080))
    else:
        return Image.new("RGBA", (1920, 1080), color=fallback_color)

def get_wrapped_text(text, font, max_width):
    lines = []
    current_line = ""
    words = []
    temp_eng = ""
    
    for char in text:
        if char.isascii() and not char.isspace():
            temp_eng += char
        else:
            if temp_eng:
                words.append(temp_eng)
                temp_eng = ""
            words.append(char)
    if temp_eng:
        words.append(temp_eng)

    for word in words:
        if word == '\n':
            lines.append(current_line)
            current_line = ""
            continue
            
        test_line = current_line + word
        if font.getlength(test_line) <= max_width:
            current_line = test_line
        else:
            if current_line.strip() == "":
                lines.append(word)
                current_line = ""
            else:
                lines.append(current_line)
                current_line = word.lstrip()
                
    if current_line:
        lines.append(current_line)
        
    return lines

def draw_scaled_text(draw, position, text, font_path, base_size, fill, max_width, anchor="mm"):
    current_size = base_size
    font = ImageFont.truetype(font_path, current_size)
    text_width = font.getlength(text)
    
    while text_width > max_width and current_size > 30:
        current_size -= 2
        font = ImageFont.truetype(font_path, current_size)
        text_width = font.getlength(text)
        
    draw.text(position, text, font=font, fill=fill, anchor=anchor)
    return font

def generate_slides():
    if not os.path.exists(JSON_FILE):
        print(f"[錯誤] 找不到 {JSON_FILE}！")
        return

    if os.path.exists(OUTPUT_FOLDER):
        shutil.rmtree(OUTPUT_FOLDER, ignore_errors=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        slides_data = json.load(f)

    try:
        font_slide_title = ImageFont.truetype(FONT_PATH_BOLD, 72)
        font_body = ImageFont.truetype(FONT_PATH_REG, 55)
    except Exception as e:
        print(f"[錯誤] 載入字型失敗: {e}")
        return

    print(f"--- 開始渲染 {len(slides_data)} 張投影片... ---")

    for i, slide in enumerate(slides_data):
        title_text = slide.get("title", "")
        points = slide.get("points", [])

        if i == 0:
            img = get_background(BG_TITLE, (20, 10, 50, 255))
            draw = ImageDraw.Draw(img)
            
            # 大標題
            title_base_size = 80
            font_title_multiline = ImageFont.truetype(FONT_PATH_BOLD, title_base_size)
            title_lines = get_wrapped_text(title_text, font_title_multiline, max_width=1750)
            
            title_y_start = 280
            line_height = title_base_size + 20 
            
            for line in title_lines:
                draw_scaled_text(draw, (1920/2, title_y_start), line, FONT_PATH_BOLD, title_base_size, fill=(220, 240, 255), max_width=1750)
                title_y_start += line_height 
            
            # Metadata
            font_meta = ImageFont.truetype(FONT_PATH_BOLD, 45)
            meta_y_start = title_y_start + 50 

            if len(points) >= 3:
                year_part = ""
                pub_part = points[1]
                if "," in points[1]:
                    parts = points[1].split(",", 1)
                    year_part = parts[0].strip()
                    pub_part = parts[1].strip()

                journal_with_year = f"{points[0]} ({year_part})" if year_part else points[0]
                
                font_used = draw_scaled_text(draw, (1920/2, meta_y_start), journal_with_year, FONT_PATH_BOLD, 45, fill=(255, 255, 255), max_width=1700)
                
                text_width = font_used.getlength(journal_with_year)
                draw.line([(1920/2 - text_width/2, meta_y_start + 40), (1920/2 + text_width/2, meta_y_start + 40)], fill=(255, 255, 255), width=4)
                
                pub_lines = get_wrapped_text(pub_part, font_meta, max_width=1600)
                pub_y = meta_y_start + 110 
                for line in pub_lines:
                    draw.text((1920/2, pub_y), line, font=font_meta, fill=(255, 255, 255), anchor="mm")
                    pub_y += 65 
                
                draw_scaled_text(draw, (1920/2, pub_y + 15), points[2], FONT_PATH_BOLD, 45, fill=(255, 255, 255), max_width=1700)

            # 講者資訊
            font_presenter = ImageFont.truetype(FONT_PATH_BOLD, 45) 
            draw.text((1920/2, 980), "Presented By: Huang Jun Chi", font=font_presenter, fill=(200, 220, 255), anchor="mm")

        else:
            img = get_background(BG_CONTENT, (20, 30, 60, 255))
            draw = ImageDraw.Draw(img)
            
            draw_scaled_text(draw, (150, 135), title_text, FONT_PATH_BOLD, 72, fill=(255, 255, 255), max_width=1650, anchor="lm")
            draw.line([(150, 210), (1770, 210)], fill=(0, 200, 255), width=4)

            start_y = 260 
            for point in points:
                bullet_y = start_y + 24
                bullet_radius = 8
                draw.ellipse(
                    [(150, bullet_y), (150 + bullet_radius*2, bullet_y + bullet_radius*2)], 
                    fill=(0, 200, 255)
                )
                
                lines = get_wrapped_text(point, font_body, max_width=1600)
                
                for line in lines:
                    draw.text((190, start_y), line, font=font_body, fill=(240, 240, 240))
                    start_y += 75
                
                start_y += 35 

        output_path = os.path.join(OUTPUT_FOLDER, f"slide_{i:02d}.png")
        img.save(output_path, "PNG")
        print(f"  [OK] 渲染完成: slide_{i:02d}.png")

    print("視覺渲染完畢！")

if __name__ == "__main__":
    generate_slides()
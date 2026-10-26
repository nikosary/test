# ==========================================================
# МОДУЛЬ ВИДЕОГЕНЕРАЦИИ ( КИНЕМАТОГРАФИЧЕСКИЙ ДВИЖОК МАКСИМА 2026 )
# ==========================================================
import os
import sys
import subprocess
from datetime import datetime

def wrap_text_clean(text, max_chars=35):
    """Аккуратно разбивает длинный текст на строки для экрана, чтобы он не вылетал за рамки."""
    if not text:
        return ""
    clean_text = str(text).replace("[", "").replace("]", "").replace("'", "").replace('"', '')
    words = clean_text.split()
    lines = []
    current_line = []
    current_length = 0
    for word in words:
        if current_length + len(word) + 1 <= max_chars:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
    if current_line:
        lines.append(" ".join(current_line))
    return "\\\n".join(lines)

def generate_video(user_query, theses_list, output_path="output.mp4"):
    """Создает профессиональный MP4-фильм с синим фоном, рамками, временем и озвучкой."""
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")
    display_time = now.strftime("%H:%M:%S")

    # Определяем пути к временным файлам звука в папке /tmp
    TEMP_DIR = "/tmp" if not sys.platform.startswith("win") else "."
    audio_file_path = os.path.join(TEMP_DIR, "audio.mp3")

    # Автоматически выбираем движок FFmpeg для Render
    ffmpeg_path = "static_ffmpeg"
    if sys.platform.startswith("win"):
        ffmpeg_path = "ffmpeg"

    # Готовим тексты: разбиваем заголовок и слайды на красивые строчки
    clean_q = user_query.replace("'", "").replace('"', "")
    if len(clean_q) > 40: 
        clean_q = clean_q[:37] + "..."
    
    q_wrapped = wrap_text_clean(clean_q, max_chars=30)
    
    # Тексты на слайдах будут строго разными по индексам элементов списка
    t1_wrapped = wrap_text_clean(theses_list[0] if len(theses_list) > 0 else "Тезис 1", max_chars=35)
    t2_wrapped = wrap_text_clean(theses_list[1] if len(theses_list) > 1 else "Тезис 2", max_chars=35)
    t3_wrapped = wrap_text_clean(theses_list[2] if len(theses_list) > 2 else "Тезис 3", max_chars=35)

    slide_time = 4.0  # Каждый экран показывается по 4 секунды
    print(f"[ДВИЖОК ВИДЕО] 🎬 Начинаю профессиональную сборку ролика через {ffmpeg_path}...")

    try:
        # Базовая команда сборки 4-х экранов (сине-зеленая гамма проекта Чистый Код)
        cmd = [
            ffmpeg_path, "-y",
            "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1a2a3d:s=854x480:r=10", 
            "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#2d5a27:s=854x480:r=10", 
            "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1e3d1a:s=854x480:r=10", 
            "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#2d2d2d:s=854x480:r=10", 
        ]
        
        # Подключаем аудиофайл озвучки, если он физически создан
        has_audio = os.path.exists(audio_file_path) and os.path.getsize(audio_file_path) > 0
        if has_audio: 
            cmd += ["-i", audio_file_path]
            print("[ДВИЖОК ВИДЕО] 🎙️ Аудиодорожка успешно найдена и добавлена в проект")

        # Накладываем красивый текст со шрифтами, границами и выравниванием по центру
        filter_string = (
            f"[0:v] drawtext=text='{q_wrapped}':fontcolor=white:fontsize=26:x=(w-text_w)/2:y=100:borderw=2:bordercolor=black [v1_title];"
            f"[v1_title] drawtext=text='ДАТА: {current_date}  ВРЕМЯ: {display_time}':fontcolor=yellow:fontsize=28:x=(w-text_w)/2:y=260:borderw=3:bordercolor=black [v1];"
            f"[1:v] drawtext=text='{t1_wrapped}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:borderw=2:bordercolor=black:line_spacing=8 [v2];"
            f"[2:v] drawtext=text='{t2_wrapped}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:borderw=2:bordercolor=black:line_spacing=8 [v3];"
            f"[3:v] drawtext=text='{t3_wrapped}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:borderw=2:bordercolor=black:line_spacing=8 [v4];"
            "[v1][v2][v3][v4] concat=n=4:v=1:a=0 [v_final]"
        )
        cmd += ["-filter_complex", filter_string, "-map", "[v_final]"]
        
        # Настраиваем аудиокодек
        if has_audio: 
            cmd += ["-map", "4:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
            
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", output_path]
        
        # Запускаем сборку
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("[ДВИЖОК ВИДЕО] 🎉 РОЛИК СМОНТИРОВАН ИДЕАЛЬНО!")
        return True
    except Exception as e:
        print(f"[ДВИЖОК ВИДЕО] ❌ Ошибка FFmpeg сборщика: {e}")
        return False

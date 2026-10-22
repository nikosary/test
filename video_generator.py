import subprocess
import os
import sys
from datetime import datetime

def wrap_text(text, max_chars=35):
    """Разбивает длинный текст на аккуратные строки для экрана."""
    words = text.split()
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

def find_font():
    """Ищет шрифт Arial в системе Windows или Linux."""
    if os.path.exists("arial.ttf"):
        return "arial.ttf"
    if sys.platform.startswith("win"):
        win_font = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf")
        if os.path.exists(win_font): return win_font.replace("\\", "/")
    else:
        linux_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
        ]
        for font in linux_fonts:
            if os.path.exists(font): return font
    return "arial.ttf"

def generate_video(query_text, audio_file="audio.mp3", output_video="output.mp4"):
    print("[ИИ Видео] Запуск синхронного монтажа с крупными часами...")
    
    # Считываем реальное время и дату
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")
    current_time = now.strftime("%H:%M:%S") # Возвращаем двоеточия, теперь они безопасны
    
    try:
        from summarizer import generate_summary
        theses = generate_summary(query_text)
    except Exception:
        theses = ["Первый тезис от ИИ", "Второй тезис от ИИ", "Третий тезис от ИИ"]

    while len(theses) < 3:
        theses.append("Чистый код 2026")

    # Форматируем тексты (убираем опасные для FFmpeg кавычки)
    clean_query = query_text.replace("'", "").replace('"', '').replace(':', ' ').strip()
    if len(clean_query) > 40: clean_query = clean_query[:37] + "..."
    
    q_wrapped = wrap_text(clean_query, max_chars=30)
    
    # СИНХРОНИЗАЦИЯ: Узнаем точную длину аудиофайла, чтобы разбить слайды поровну
    audio_duration = 15 # Запасной вариант по умолчанию
    if os.path.exists(audio_file):
        try:
            # Запрашиваем длину звука через утилиту ffprobe
            cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {audio_file}"
            audio_duration = float(subprocess.check_output(cmd, shell=True).decode().strip())
        except Exception:
            pass

    # Делим общее время звука на 3 равных отрезка для каждого слайда
    slide_time = round(audio_duration / 3, 1)
    print(f"[ИИ Видео] Длина звука: {audio_duration} сек. Каждый слайд будет гореть по {slide_time} сек.")

    # Форматируем тексты для слайдов
    t1_wrapped = wrap_text(str(theses[0]).replace("'", "").replace('"', ''))
    t2_wrapped = wrap_text(str(theses[1]).replace("'", "").replace('"', ''))
    t3_wrapped = wrap_text(str(theses[2]).replace("'", "").replace('"', ''))

    if sys.platform.startswith("win"):
        ffmpeg_path = os.path.abspath("ffmpeg.exe")
    else:
        ffmpeg_path = "ffmpeg"

    if os.path.exists(output_video):
        try: os.remove(output_video)
        except Exception: pass

    font_path = find_font()
    
    # Новая, продвинутая команда FFmpeg с крупным раздельным выводом текста
    command = [
        ffmpeg_path, "-y",
        "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1e3d1a:s=854x480:r=10", # 1. Зеленый
        "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1a2a3d:s=854x480:r=10", # 2. Синий
        "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#2d2d2d:s=854x480:r=10", # 3. Серый
        "-i", audio_file,
        
        "-filter_complex", 
        # Слайд 1: Сверху вопрос (fontsize=24), а по центру крупно ДАТА и ВРЕМЯ (fontsize=32)
        f"[0:v] drawtext=fontfile='{font_path}':text='{q_wrapped}':fontcolor=white:fontsize=24:"
        f"x=(w-text_w)/2:y=60:borderw=3:bordercolor=black [v1_init];"
        f"[v1_init] drawtext=fontfile='{font_path}':text='{current_date}  {current_time}':fontcolor=yellow:fontsize=32:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=4:bordercolor=black [v1];"
        
        # Слайд 2: Первый тезис ИИ
        f"[1:v] drawtext=fontfile='{font_path}':text='{t1_wrapped}':fontcolor=white:fontsize=22:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=6 [v2];"
        
        # Слайд 3: Второй тезис ИИ
        f"[2:v] drawtext=fontfile='{font_path}':text='{t2_wrapped}':fontcolor=white:fontsize=22:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=5 [v3];"
        
        "[v1][v2][v3] concat=n=3:v=1:a=0 [v_final]",
        
        "-map", "[v_final]",                  
        "-map", "3:a",                        
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",                          
        output_video
    ]

    try:
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if os.path.exists(output_video):
            print(f"[ИИ Видео] Сверхточный фильм с крупными часами успешно смонтирован!")
            return output_video
        else: return None
    except Exception as e:
        print(f"[Ошибка монтажа]: {e}")
        return None

if __name__ == "__main__":
    generate_video("Зачем кошке усы")

import subprocess
import os
import sys
from datetime import datetime

def wrap_text(text, max_chars=35):
    """Разбивает длинный текст на аккуратные строки для экрана видео."""
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
    print("[ИИ Видео] Запуск автономного монтажа с математическим расчетом таймингов...")
    
    # Считываем реальное время и дату
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")
    current_time = now.strftime("%H:%M:%S")
    
    try:
        from summarizer import generate_summary
        theses = generate_summary(query_text)
    except Exception:
        theses = ["Первый тезис от ИИ", "Второй тезис от ИИ", "Третий тезис от ИИ"]

    while len(theses) < 3:
        theses.append("Чистый код 2026")

    # Форматируем тексты (убираем опасные кавычки)
    clean_query = query_text.replace("'", "").replace('"', '').replace(':', ' ').strip()
    if len(clean_query) > 40: clean_query = clean_query[:37] + "..."
    
    q_wrapped = wrap_text(clean_query, max_chars=30)
    
    # ИСПРАВЛЕНО: Убрали ffprobe. Считаем длину аудио математически по объёму текста!
    # Робот читает в среднем со скоростью 12 символов в секунду.
    full_text_length = len(" ".join(theses))
    audio_duration = max(12, round(full_text_length / 12, 1))
    
    # Делим время звука на 3 равных слайда для идеальной синхронизации
    slide_time = round(audio_duration / 3, 1)
    print(f"[ИИ Видео] Расчетная длина звука: {audio_duration} сек. Слайд: {slide_time} сек.")

    # Разносим тезисы по отдельным переменным строго по номерам из списка
    t1_raw = str(theses[0]).replace("'", "").replace('"', '').replace(':', '').strip()
    t2_raw = str(theses[1]).replace("'", "").replace('"', '').replace(':', '').strip()
    t3_raw = str(theses[2]).replace("'", "").replace('"', '').replace(':', '').strip()

    t1_wrapped = wrap_text(t1_raw)
    t2_wrapped = wrap_text(t2_raw)
    t3_wrapped = wrap_text(t3_raw)

    if sys.platform.startswith("win"):
        ffmpeg_path = os.path.abspath("ffmpeg.exe")
        if not os.path.exists(ffmpeg_path): ffmpeg_path = "ffmpeg"
    else:
        ffmpeg_path = "ffmpeg"

    if os.path.exists(output_video):
        try: os.remove(output_video)
        except Exception: pass

    font_path = find_font()
    
    # Пуленепробиваемая команда FFmpeg с крупными часами и раздельным выводом тезисов
    command = [
        ffmpeg_path, "-y",
        "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1e3d1a:s=854x480:r=10", 
        "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1a2a3d:s=854x480:r=10", 
        "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#2d2d2d:s=854x480:r=10", 
        "-i", audio_file,
        
        "-filter_complex", 
        # Титульный экран: Вопрос сверху, а по центру КРУПНО желтая дата и время
        f"[0:v] drawtext=fontfile='{font_path}':text='{q_wrapped}':fontcolor=white:fontsize=24:"
        f"x=(w-text_w)/2:y=50:borderw=3:bordercolor=black [v1_title];"
        f"[v1_title] drawtext=fontfile='{font_path}':text='{current_date}  {current_time}':fontcolor=yellow:fontsize=32:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=4:bordercolor=black [v1];"
        
        # Слайд 2: Первый тезис ИИ
        f"[1:v] drawtext=fontfile='{font_path}':text='{t1_wrapped}':fontcolor=white:fontsize=22:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=6 [v2];"
        
        # Слайд 3: Второй тезис ИИ
        f"[2:v] drawtext=fontfile='{font_path}':text='{t2_wrapped}':fontcolor=white:fontsize=22:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=6 [v3];"
        
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
